import json
import os
import re
from typing import Any, Dict, List, Tuple, Optional
from utils.agent_workflow import run_workflow


PreferredOrder: Tuple[str, ...] = (
    "data-test-id",
    "data-testid",
    "aria-label",
    "role",
    "name",
    "type",
    "id",
    "class",
)


def _extract_attributes(html: str) -> List[Dict[str, str]]:
    """Very lightweight attribute harvesting without external parsers.

    Finds elements that carry preferred attributes and returns a list of
    {tag, attr, value} entries.
    """
    results: List[Dict[str, str]] = []

    # Find tags with attributes of interest; basic regex scanning
    # This is a heuristic and not a full HTML parser.
    tag_pattern = re.compile(r"<([a-zA-Z0-9_-]+)([^>]*)>")
    attr_patterns = {attr: re.compile(fr"{re.escape(attr)}=\"([^\"]+)\"") for attr in PreferredOrder}

    for tag_match in tag_pattern.finditer(html):
        tag = tag_match.group(1)
        attrs_blob = tag_match.group(2)
        for attr, pat in attr_patterns.items():
            m = pat.search(attrs_blob)
            if m:
                results.append({"tag": tag, "attr": attr, "value": m.group(1)})
    return results


def _score_for(attr: str, unique: bool) -> float:
    base_weight = {
        "data-test-id": 0.95,
        "data-testid": 0.93,
        "aria-label": 0.88,
        "role": 0.82,
        "name": 0.80,
        "type": 0.72,
        "id": 0.70,
        "class": 0.55,
    }.get(attr, 0.5)
    return round(base_weight + (0.04 if unique else 0.0), 3)


def _build_css_selector(tag: str, attr: str, value: str) -> str:
    safe_value = value.replace(" ", "\\ ")
    if attr in ("class",):
        # Use first class token for minimal selector
        first_class = value.strip().split()[0]
        return f"{tag}.{first_class}"
    if attr in ("id",):
        return f"{tag}#{value}"
    return f"{tag}[{attr}='{safe_value}']"


def generate_candidates_from_dom(dom_html: str) -> List[Dict[str, Any]]:
    harvested = _extract_attributes(dom_html)
    # Count attribute-value pairs to infer uniqueness
    counts: Dict[Tuple[str, str], int] = {}
    for item in harvested:
        key = (item["attr"], item["value"])
        counts[key] = counts.get(key, 0) + 1

    candidates: List[Dict[str, Any]] = []
    for item in harvested:
        key = (item["attr"], item["value"])
        unique = counts.get(key, 0) == 1
        selector = _build_css_selector(item["tag"], item["attr"], item["value"])
        score = _score_for(item["attr"], unique)
        candidates.append(
            {
                "selector": selector,
                "strategy": "css",
                "attributes_used": [{"attr": item["attr"], "value": item["value"]}],
                "stability_score": score,
                "confidence": score,
                "rationale": f"Based on {item['attr']} attribute; unique={unique}",
            }
        )

    # Sort by score descending and deduplicate by selector
    seen = set()
    sorted_unique: List[Dict[str, Any]] = []
    for c in sorted(candidates, key=lambda x: x["stability_score"], reverse=True):
        if c["selector"] in seen:
            continue
        seen.add(c["selector"])
        sorted_unique.append(c)
    return sorted_unique[:10]


class HeuristicAnalyzer:
    def analyze(self, ctx: Dict[str, Any], dom_html: str) -> Dict[str, Any]:
        candidates = generate_candidates_from_dom(dom_html)
        return {
            "source": "heuristic",
            "candidates": candidates,
        }


class AgentAnalyzer:
    """Agent-first analyzer placeholder. Intended to run a LangGraph workflow.

    For now, it delegates to heuristic as a fallback to keep local CLI runnable
    without external dependencies. This class is the seam to integrate
    LangGraph/LangChain later.
    """

    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        self.model = model
        self.temperature = temperature

    def analyze(self, ctx: Dict[str, Any], dom_html: str) -> Dict[str, Any]:
        try:
            # Use agent workflow to re-rank heuristic candidates for now.
            seed_candidates = generate_candidates_from_dom(dom_html)
            graph_result = run_workflow(ctx, dom_html, {"ai": {"confidence_threshold": 0.8}}, seed_candidates)
            if graph_result.get("candidates"):
                return graph_result
            return {
                "source": "agent_graph_empty",
                "candidates": seed_candidates,
            }
        except Exception:
            # Hard fallback to heuristic if agent path fails
            candidates = generate_candidates_from_dom(dom_html)
            return {
                "source": "heuristic_fallback",
                "candidates": candidates,
            }


def _select_analyzer(settings: Optional[Dict[str, Any]]) -> Any:
    ai_enabled = bool(settings.get("ai", {}).get("enabled", True)) if settings else True
    if ai_enabled:
        model = settings.get("ai", {}).get("model") if settings else None
        temp = float(settings.get("ai", {}).get("temperature", 0.0)) if settings else 0.0
        return AgentAnalyzer(model=model, temperature=temp)
    return HeuristicAnalyzer()


def _validate_and_rank(candidates: List[Dict[str, Any]], confidence_threshold: float) -> List[Dict[str, Any]]:
    filtered = [c for c in candidates if float(c.get("confidence", 0.0)) >= confidence_threshold]
    if not filtered:
        filtered = candidates[:3]
    return filtered


def analyze_context(context_path: str, settings: Optional[Dict[str, Any]] = None) -> str:
    """Load healing context, read DOM, run analyzer (agent-first), emit candidates JSON sidecar. Returns path."""
    with open(context_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    dom_path = ctx.get("dom_snapshot_path", "")
    out_path = context_path.replace("_context.json", "_candidates.json")
    if not dom_path or not os.path.exists(dom_path):
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "source": "no_dom",
                "candidates": [],
                "source_context": os.path.basename(context_path)
            }, f, indent=2)
        return out_path

    with open(dom_path, "r", encoding="utf-8") as f:
        dom_html = f.read()

    analyzer = _select_analyzer(settings)
    result = analyzer.analyze(ctx, dom_html)
    confidence_threshold = float(settings.get("ai", {}).get("confidence_threshold", 0.8)) if settings else 0.8
    ranked = _validate_and_rank(result.get("candidates", []), confidence_threshold)

    out = {
        "source": result.get("source", "unknown"),
        "source_context": os.path.basename(context_path),
        "url": ctx.get("url", ""),
        "action": ctx.get("action", ""),
        "locator_before": ctx.get("locator"),
        "confidence_threshold": confidence_threshold,
        "candidates": ranked,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out_path


