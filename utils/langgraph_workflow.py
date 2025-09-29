import json
from typing import Any, Dict, List, Optional, TypedDict

try:
    from langgraph.graph import StateGraph, END
    _LANGGRAPH_AVAILABLE = True
except Exception:
    _LANGGRAPH_AVAILABLE = False

try:
    # Optional LLM providers via LangChain wrappers
    from langchain_openai import ChatOpenAI  # type: ignore
except Exception:
    ChatOpenAI = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic  # type: ignore
except Exception:
    ChatAnthropic = None  # type: ignore


class HealingState(TypedDict, total=False):
    error_info: Dict[str, Any]
    dom_snapshot: str
    screenshot_path: str
    original_locator: Optional[str]
    candidate_locators: List[Dict[str, Any]]
    validated_locators: List[Dict[str, Any]]
    selected_locator: Optional[Dict[str, Any]]
    confidence_score: float
    attempt: int
    max_attempts: int
    fallback_used: bool
    human_required: bool
    logs: List[str]


def _append_log(state: HealingState, message: str) -> None:
    logs = state.get("logs", []) or []
    logs.append(message)
    state["logs"] = logs


def _get_llm(settings: Optional[Dict[str, Any]]):
    if not settings:
        return None
    ai = settings.get("ai", {})
    provider = (ai.get("provider") or "").lower()
    model = ai.get("model")
    temperature = float(ai.get("temperature", 0.0))
    if provider == "openai" and ChatOpenAI is not None and model:
        return ChatOpenAI(model=model, temperature=temperature)
    if provider == "anthropic" and ChatAnthropic is not None and model:
        return ChatAnthropic(model=model, temperature=temperature)
    return None


def node_error_analysis(state: HealingState, settings: Optional[Dict[str, Any]]) -> HealingState:
    try:
        err = state.get("error_info", {})
        dom_present = bool(state.get("dom_snapshot"))
        _append_log(state, f"error_analysis: dom_present={dom_present}, error={err.get('message','')}.")
        # LLM can summarize/label error type; optional
        llm = _get_llm(settings)
        if llm is not None:
            # Keep inputs concise for cost; prompt engineered for locator issues
            prompt = (
                "You are a test automation assistant. Classify the error cause "
                "(invalid_locator|timing|stale) based on the message and stack.\n\n"
                f"Message: {err.get('message','')}\nStack: {err.get('stack','')}"
            )
            try:
                resp = llm.invoke(prompt)  # type: ignore
                label = getattr(resp, "content", "").strip().split()[0].lower()
                state.setdefault("error_info", {})["ai_label"] = label
                _append_log(state, f"error_analysis: ai_label={label}")
            except Exception as e:
                _append_log(state, f"error_analysis: llm_failed={e}")
        return state
    except Exception as e:
        _append_log(state, f"error_analysis: failed {e}")
        return state


def node_locator_generation(state: HealingState, settings: Optional[Dict[str, Any]]) -> HealingState:
    try:
        dom = state.get("dom_snapshot", "")
        candidates: List[Dict[str, Any]] = state.get("candidate_locators", []) or []
        # Strategy 1: Prefer data-test-id / data-testid
        import re
        for attr in ["data-test-id", "data-testid", "aria-label", "role", "name", "type", "id", "class"]:
            pattern = re.compile(fr"<([a-zA-Z0-9_-]+)([^>]*){attr}=\"([^\"]+)\"", re.IGNORECASE)
            for m in pattern.finditer(dom):
                tag, _, value = m.group(1), m.group(2), m.group(3)
                selector = _build_css_selector(tag, attr.lower(), value)
                cand = {
                    "selector": selector,
                    "strategy": "css",
                    "attributes_used": [{"attr": attr.lower(), "value": value}],
                    "stability_score": _base_score(attr.lower()),
                    "confidence": _base_score(attr.lower()),
                    "rationale": f"Derived from {attr}",
                }
                candidates.append(cand)

        # Optionally augment via LLM to propose XPath/CSS
        llm = _get_llm(settings)
        if llm is not None:
            try:
                prompt = (
                    "Given a DOM fragment, propose up to 5 robust selectors (CSS preferred, XPath as last resort)\n"
                    "Prefer data-* and semantic attributes; avoid brittle absolute XPaths.\n"
                    "Return JSON list with fields selector,strategy,rationale.\nDOM:\n" + dom[:5000]
                )
                resp = llm.invoke(prompt)  # type: ignore
                text = getattr(resp, "content", "").strip()
                proposed = []
                try:
                    proposed = json.loads(text)
                except Exception:
                    # If not JSON, skip
                    proposed = []
                for p in proposed:
                    s = str(p.get("selector", ""))
                    strat = p.get("strategy", "css")
                    if not s:
                        continue
                    candidates.append({
                        "selector": s,
                        "strategy": strat,
                        "attributes_used": [],
                        "stability_score": 0.75,
                        "confidence": 0.75,
                        "rationale": f"LLM proposal: {p.get('rationale','')}",
                    })
            except Exception as e:
                _append_log(state, f"locator_generation: llm_failed={e}")

        # Deduplicate by selector
        seen = set()
        dedup: List[Dict[str, Any]] = []
        for c in sorted(candidates, key=lambda x: x.get("stability_score", 0.0), reverse=True):
            if c["selector"] in seen:
                continue
            seen.add(c["selector"])
            dedup.append(c)
        state["candidate_locators"] = dedup[:15]
        _append_log(state, f"locator_generation: produced={len(state['candidate_locators'])}")
        return state
    except Exception as e:
        _append_log(state, f"locator_generation: failed {e}")
        return state


def _base_score(attr: str) -> float:
    weights = {
        "data-test-id": 0.95,
        "data-testid": 0.93,
        "aria-label": 0.88,
        "role": 0.82,
        "name": 0.80,
        "type": 0.72,
        "id": 0.70,
        "class": 0.55,
    }
    return weights.get(attr, 0.5)


def _build_css_selector(tag: str, attr: str, value: str) -> str:
    safe = value.replace(" ", "\\ ")
    if attr == "class":
        first_class = value.strip().split()[0]
        return f"{tag}.{first_class}"
    if attr == "id":
        return f"{tag}#{value}"
    return f"{tag}[{attr}='{safe}']"


def node_validation(state: HealingState, settings: Optional[Dict[str, Any]]) -> HealingState:
    try:
        dom = state.get("dom_snapshot", "")
        validated: List[Dict[str, Any]] = []
        import re
        for c in state.get("candidate_locators", []) or []:
            sel = c.get("selector", "")
            if not sel:
                continue
            # Heuristic validation: count attribute presence tokens
            score_bonus = 0.0
            m_attr = re.findall(r"\[([^=]+)='([^']+)'\]", sel)
            matches = 0
            for (a, v) in m_attr:
                if v in dom:
                    matches += 1
                    score_bonus += 0.01
            c2 = dict(c)
            c2["confidence"] = float(c.get("confidence", 0.0)) + score_bonus
            c2["validation_notes"] = f"attr_matches={matches}"
            validated.append(c2)
        state["validated_locators"] = validated
        _append_log(state, f"validation: validated={len(validated)}")
        return state
    except Exception as e:
        _append_log(state, f"validation: failed {e}")
        return state


def node_ranking(state: HealingState, settings: Optional[Dict[str, Any]]) -> HealingState:
    try:
        ranked = sorted(state.get("validated_locators", []) or [], key=lambda x: x.get("confidence", 0.0), reverse=True)
        state["validated_locators"] = ranked
        _append_log(state, f"ranking: top_confidence={ranked[0]['confidence'] if ranked else 'n/a'}")
        return state
    except Exception as e:
        _append_log(state, f"ranking: failed {e}")
        return state


def node_selection(state: HealingState, settings: Optional[Dict[str, Any]]) -> HealingState:
    try:
        threshold = float(settings.get("ai", {}).get("confidence_threshold", 0.8)) if settings else 0.8
        llm = _get_llm(settings)
        top = (state.get("validated_locators", []) or [])[:5]
        chosen: Optional[Dict[str, Any]] = top[0] if top else None
        if llm is not None and top:
            try:
                prompt = (
                    "Choose the best locator candidate based on stability and semantics.\n"
                    f"Threshold: {threshold}. Return JSON with keys selected_index, rationale.\nCandidates: "
                    + json.dumps(top)
                )
                resp = llm.invoke(prompt)  # type: ignore
                text = getattr(resp, "content", "").strip()
                data = json.loads(text)
                idx = int(data.get("selected_index", 0))
                if 0 <= idx < len(top):
                    chosen = top[idx]
                    chosen["rationale"] = f"LLM: {data.get('rationale','')}"
            except Exception as e:
                _append_log(state, f"selection: llm_failed={e}")

        state["selected_locator"] = chosen
        state["confidence_score"] = float(chosen.get("confidence", 0.0)) if chosen else 0.0
        state["human_required"] = state["confidence_score"] < threshold
        _append_log(state, f"selection: confidence={state['confidence_score']} human_required={state['human_required']}")
        return state
    except Exception as e:
        _append_log(state, f"selection: failed {e}")
        return state


def build_workflow(settings: Optional[Dict[str, Any]] = None):
    if not _LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph not available. Please install 'langgraph'.")
    graph = StateGraph(HealingState)

    # Register nodes (functions take state and settings)
    graph.add_node("error_analysis", lambda s: node_error_analysis(s, settings))
    graph.add_node("locator_generation", lambda s: node_locator_generation(s, settings))
    graph.add_node("validation", lambda s: node_validation(s, settings))
    graph.add_node("ranking", lambda s: node_ranking(s, settings))
    graph.add_node("selection", lambda s: node_selection(s, settings))

    # Edges
    graph.set_entry_point("error_analysis")
    graph.add_edge("error_analysis", "locator_generation")
    graph.add_edge("locator_generation", "validation")
    graph.add_edge("validation", "ranking")
    graph.add_edge("ranking", "selection")

    # Conditional edges from selection
    def next_step(state: HealingState) -> str:
        attempt = int(state.get("attempt", 1) or 1)
        max_attempts = int(state.get("max_attempts", 3) or 3)
        selected = state.get("selected_locator")
        human_required = bool(state.get("human_required", False))
        if (not selected) and attempt < max_attempts:
            state["attempt"] = attempt + 1
            state["fallback_used"] = True
            _append_log(state, "conditional: retrying locator_generation due to no selection")
            return "locator_generation"
        if human_required:
            # End but flagged for human in the loop
            _append_log(state, "conditional: human_in_loop")
            return END
        return END

    graph.add_conditional_edges("selection", next_step)
    return graph.compile()


def run_langgraph_workflow(
    error_info: Dict[str, Any],
    dom_snapshot: str,
    screenshot_path: str,
    original_locator: Optional[str],
    settings: Optional[Dict[str, Any]] = None,
) -> HealingState:
    if not _LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph not available. Please install 'langgraph'.")
    wf = build_workflow(settings)
    init: HealingState = {
        "error_info": error_info,
        "dom_snapshot": dom_snapshot,
        "screenshot_path": screenshot_path,
        "original_locator": original_locator,
        "candidate_locators": [],
        "validated_locators": [],
        "attempt": 1,
        "max_attempts": int((settings or {}).get("healing", {}).get("max_attempts", 3)),
        "fallback_used": False,
        "logs": [],
    }
    final_state: HealingState = wf.invoke(init)  # type: ignore
    return final_state




