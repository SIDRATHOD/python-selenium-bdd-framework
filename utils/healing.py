import json
import os
import time
from typing import Any, Dict, Optional, Tuple, List
from selenium.webdriver.common.by import By
from utils.ai_analysis import analyze_context
try:
    from utils.langgraph_workflow import run_langgraph_workflow  # type: ignore
    _HAS_LANGGRAPH = True
except Exception:
    _HAS_LANGGRAPH = False
from utils.auto_fix import apply_locator_fix
from utils.healing_report import write_report_entry


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _sanitize_for_filename(text: str) -> str:
    # Replace any Windows-unsafe characters with underscore
    # Disallow: < > : " / \\ | ? * and also spaces, quotes, commas
    unsafe = set('<>:"/\\|?*\n\r\t\0')
    sanitized = []
    for ch in text:
        if ch in unsafe or ord(ch) < 32:
            sanitized.append('_')
        else:
            # Keep only a safe subset
            if ch.isalnum() or ch in ['-', '_', '.', '[', ']', ',']:
                sanitized.append(ch)
            else:
                sanitized.append('_')
    out = ''.join(sanitized)
    # Collapse long names
    return out[:80]


def capture_artifacts(
    driver: Any,
    report_dir: str,
    artifact_stem: str,
) -> Tuple[str, str]:
    """Save DOM snapshot and screenshot. Returns (dom_path, screenshot_path)."""
    screenshots_dir = os.path.join(report_dir, "screenshots")
    self_healing_dir = os.path.join(report_dir, "self_healing")

    _ensure_dir(screenshots_dir)
    _ensure_dir(self_healing_dir)

    ts = _timestamp()
    dom_path = os.path.join(self_healing_dir, f"{artifact_stem}_{ts}.html")
    screenshot_path = os.path.join(screenshots_dir, f"{artifact_stem}_{ts}.png")

    try:
        html = driver.page_source
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        dom_path = ""

    try:
        driver.save_screenshot(screenshot_path)
    except Exception:
        screenshot_path = ""

    return dom_path, screenshot_path


def record_failure(
    driver: Any,
    logger: Any,
    report_dir: str,
    action: str,
    locator: Optional[Any],
    exception: Exception,
) -> str:
    """Capture artifacts and write a minimal healing context JSON. Returns context path."""
    self_healing_dir = os.path.join(report_dir, "self_healing")
    _ensure_dir(self_healing_dir)

    raw = f"{action}__{str(locator)}"
    artifact_stem = _sanitize_for_filename(raw)
    dom_path, screenshot_path = capture_artifacts(driver, report_dir, artifact_stem)

    context: Dict[str, Any] = {
        "timestamp": _timestamp(),
        "url": getattr(driver, "current_url", ""),
        "action": action,
        "locator": str(locator) if locator is not None else None,
        "exception_type": exception.__class__.__name__,
        "exception_message": str(exception),
        "dom_snapshot_path": dom_path,
        "screenshot_path": screenshot_path,
    }

    context_path = os.path.join(self_healing_dir, f"{artifact_stem}_{_timestamp()}_context.json")
    try:
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2)
        logger.error(f"Self-healing context saved: {context_path}")
    except Exception as e:
        logger.error(f"Failed to write healing context JSON: {e}")

    return context_path


def _perform_action_with_selector(driver: Any, action: str, strategy: str, selector: str, action_kwargs: Optional[Dict[str, Any]] = None) -> bool:
    action_kwargs = action_kwargs or {}
    try:
        if strategy == "css":
            by = By.CSS_SELECTOR
        elif strategy == "xpath":
            by = By.XPATH
        else:
            by = By.CSS_SELECTOR

        if action == "click":
            elem = driver.find_element(by, selector)
            elem.click()
            return True
        if action == "send_keys":
            text = action_kwargs.get("text", "")
            elem = driver.find_element(by, selector)
            elem.clear()
            elem.send_keys(text)
            return True
        if action == "get_text":
            elem = driver.find_element(by, selector)
            _ = elem.text
            return True
    except Exception:
        return False
    return False


def _write_candidates_json(context_path: str, source: str, ctx: Dict[str, Any], candidates: List[Dict[str, Any]]) -> str:
    out_path = context_path.replace("_context.json", "_candidates.json")
    out = {
        "source": source,
        "source_context": os.path.basename(context_path),
        "url": ctx.get("url", ""),
        "action": ctx.get("action", ""),
        "locator_before": ctx.get("locator"),
        "candidates": candidates,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out_path


def attempt_self_heal(
    driver: Any,
    logger: Any,
    report_dir: str,
    action: str,
    locator: Any,
    action_kwargs: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Capture context, run agent workflow, try candidates locally, and persist code fix.

    Returns True if healed action succeeds locally, else False.
    """
    # 1) Capture artifacts and context
    try:
        class Dummy(Exception):
            pass
        ctx_path = record_failure(driver, logger, report_dir, action=action, locator=locator, exception=Dummy("self_heal_trigger"))
    except Exception:
        return False

    # Load context
    try:
        with open(ctx_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)
    except Exception:
        return False

    dom_path = ctx.get("dom_snapshot_path")
    try:
        dom_html = open(dom_path, "r", encoding="utf-8").read() if dom_path and os.path.exists(dom_path) else ""
    except Exception:
        dom_html = ""

    candidates: List[Dict[str, Any]] = []
    # 2) Analysis via LangGraph if available, else heuristic
    try:
        if _HAS_LANGGRAPH and dom_html:
            lg_state = run_langgraph_workflow(
                error_info={"message": ctx.get("exception_message", ""), "stack": ""},
                dom_snapshot=dom_html,
                screenshot_path=ctx.get("screenshot_path", ""),
                original_locator=ctx.get("locator"),
                settings=settings,
            )
            selected = lg_state.get("selected_locator")
            validated = lg_state.get("validated_locators") or []
            if selected:
                candidates.append(selected)
            candidates.extend(validated)
            cand_path = _write_candidates_json(ctx_path, source="langgraph", ctx=ctx, candidates=candidates)
        else:
            cand_path = analyze_context(ctx_path, settings)
            with open(cand_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                candidates = data.get("candidates", [])
    except Exception as e:
        logger.error(f"Self-heal analysis failed: {e}")
        return False

    if not candidates:
        return False

    # 3) Try candidates locally without code changes first
    attempts = 0
    max_attempts = int((settings or {}).get("healing", {}).get("max_attempts", 3))
    for cand in candidates:
        if attempts >= max_attempts:
            break
        ok = _perform_action_with_selector(driver, action, cand.get("strategy", "css"), cand.get("selector", ""), action_kwargs)
        attempts += 1
        if ok:
            # 4) Persist code fix
            try:
                audit = apply_locator_fix(cand_path, logger=logger)
                write_report_entry(report_dir, {
                    "action": action,
                    "url": ctx.get("url", ""),
                    "locator_before": ctx.get("locator"),
                    "selected": cand,
                    "audit": audit,
                    "status": "healed"
                })
            except Exception as e:
                logger.error(f"Persisting code fix failed: {e}")
            return True

    # Record failure for manual intervention
    try:
        write_report_entry(report_dir, {
            "action": action,
            "url": ctx.get("url", ""),
            "locator_before": ctx.get("locator"),
            "candidates_tried": attempts,
            "status": "manual_required"
        })
    except Exception:
        pass
    return False


