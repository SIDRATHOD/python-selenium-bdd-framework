import os
import subprocess
from typing import Any, Dict, Optional
from utils.healing_report import write_report_entry


def rerun_scenario(
    feature_path: str,
    scenario_name: Optional[str],
    report_dir: str,
    env: Optional[Dict[str, str]] = None,
) -> int:
    """Re-run a feature or specific scenario using behave. Returns process exit code.

    If scenario_name is provided, uses behave's name filter: -n "Scenario Name".
    """
    cmd = ["behave", feature_path]
    if scenario_name:
        cmd.extend(["-n", scenario_name])

    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env_vars, cwd=os.getcwd())
        code = proc.returncode
        write_report_entry(report_dir, {
            "type": "rerun",
            "feature": feature_path,
            "scenario": scenario_name,
            "exit_code": code,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        })
        return code
    except Exception as e:
        write_report_entry(report_dir, {
            "type": "rerun_error",
            "feature": feature_path,
            "scenario": scenario_name,
            "error": str(e),
        })
        return 1




