import json
import os
import time
from typing import Any, Dict


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_report_entry(report_dir: str, entry: Dict[str, Any]) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(report_dir, "self_healing")
    _ensure_dir(out_dir)
    report_path = os.path.join(out_dir, "healing_report.json")
    data = []
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except Exception:
            data = []
    entry["timestamp"] = ts
    data.append(entry)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return report_path




