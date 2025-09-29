from typing import Any, Dict, List

# LangGraph-style scaffold (no external dependency). Nodes are pure functions.

def node_load_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"context": ctx}


def node_tokenize_dom(state: Dict[str, Any], dom_html: str) -> Dict[str, Any]:
    # Minimal tokenization: attributes and text length
    tokens = {
        "length": len(dom_html),
        "has_data_test": ("data-test" in dom_html) or ("data-testid" in dom_html),
        "has_aria": ("aria-" in dom_html),
    }
    state["dom_tokens"] = tokens
    state["dom_html"] = dom_html
    return state


def node_agent_reason(state: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder reasoning: produce hints/preferences based on tokens
    tokens = state.get("dom_tokens", {})
    prefs: List[str] = []
    if tokens.get("has_data_test"):
        prefs.append("data-test-id")
        prefs.append("data-testid")
    if tokens.get("has_aria"):
        prefs.append("aria-label")
    prefs.extend(["role", "name", "type", "id", "class"])
    state["selector_preferences"] = prefs
    return state


def node_rank_candidates(state: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    prefs = state.get("selector_preferences", [])
    def score(c: Dict[str, Any]) -> float:
        # Boost score when attributes_used include higher-preference attrs
        attrs = [a.get("attr") for a in c.get("attributes_used", [])]
        boost = 0.0
        for a in attrs:
            if a in prefs:
                boost += 0.02
        return float(c.get("stability_score", 0.0)) + boost

    ranked = sorted(candidates, key=score, reverse=True)
    state["ranked_candidates"] = ranked
    return state


def node_validate(state: Dict[str, Any], confidence_threshold: float) -> Dict[str, Any]:
    ranked = state.get("ranked_candidates", [])
    filtered = [c for c in ranked if float(c.get("confidence", 0.0)) >= confidence_threshold]
    if not filtered:
        filtered = ranked[:3]
    state["final_candidates"] = filtered
    return state


def run_workflow(ctx: Dict[str, Any], dom_html: str, config: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = node_load_context(ctx)
    state = node_tokenize_dom(state, dom_html)
    state = node_agent_reason(state)
    state = node_rank_candidates(state, candidates)
    threshold = float(config.get("ai", {}).get("confidence_threshold", 0.8)) if config else 0.8
    state = node_validate(state, threshold)
    return {
        "source": "agent_graph",
        "candidates": state.get("final_candidates", []),
        "selector_preferences": state.get("selector_preferences", []),
    }




