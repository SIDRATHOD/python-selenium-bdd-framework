import json
import os
import re
from typing import Any, Dict, Optional


BY_MAP = {
    "css": "By.CSS_SELECTOR",
    "xpath": "By.XPATH",
}


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _find_locator_file(locator_str: str) -> Optional[str]:
    # Naive mapping based on known files
    candidates = [
        os.path.join("locator", "auth_locators.py"),
        os.path.join("locator", "profile_locators.py"),
    ]
    for p in candidates:
        if os.path.exists(p):
            src = _read(p)
            if locator_str in src:
                return p
    return None


def apply_locator_fix(candidates_json_path: str, logger: Any = None) -> Optional[Dict[str, Any]]:
    """Apply the highest-ranked candidate by editing the corresponding locator file.

    Returns an audit dict with before/after if an edit was made, otherwise None.
    """
    data = json.loads(_read(candidates_json_path))
    cand_list = data.get("candidates", [])
    if not cand_list:
        if logger: logger.error("No candidates to apply.")
        return None

    chosen = cand_list[0]
    selector = str(chosen.get("selector", ""))
    strategy = str(chosen.get("strategy", "css")).lower()
    original = data.get("locator_before") or ""
    if not original:
        if logger: logger.error("Missing original locator string; cannot map to file.")
        return None

    locator_file = _find_locator_file(original)
    if not locator_file:
        if logger: logger.error("Could not locate source file for the original locator.")
        return None

    src = _read(locator_file)
    before_hash = hash(src)

    # Replace tuple like (By.ID, "value") or (By.XPATH, "...") with new By
    # We try to find the exact original string first; else do a By.* tuple replacement
    if original in src:
        new_tuple = f"({BY_MAP.get(strategy, 'By.CSS_SELECTOR')}, \"{selector}\")"
        new_src = src.replace(original, new_tuple)
    else:
        # Fallback: replace the first By.* tuple on the same line as the symbol using a loose regex
        tuple_pat = re.compile(r"\(By\.[A-Z_]+,\s*\"[^\"]*\"\)")
        new_src = tuple_pat.sub(f"({BY_MAP.get(strategy, 'By.CSS_SELECTOR')}, \"{selector}\")", src, count=1)

    if new_src == src:
        if logger: logger.error("Auto-fix did not modify the source; aborting.")
        return None

    _write(locator_file, new_src)
    after_hash = hash(new_src)

    audit = {
        "file": locator_file,
        "locator_before": original,
        "locator_after": f"({BY_MAP.get(strategy, 'By.CSS_SELECTOR')}, \"{selector}\")",
        "before_hash": before_hash,
        "after_hash": after_hash,
        "strategy": strategy,
        "selector": selector,
    }
    if logger: logger.info(f"Applied locator fix in {locator_file}")
    return audit




