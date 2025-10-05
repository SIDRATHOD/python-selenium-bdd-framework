import os
import time
import logging
import json
from selenium.webdriver.common.by import By
from utils.ai_provider import get_ai_suggestion
from utils.code_fixer import rewrite_locator_file # Import the new fixer

# ... (logger config remains the same)
logger = logging.getLogger(__name__)

class Healer:
    # ... (__init__ and collect_artifacts remain the same)
    def __init__(self, driver, locator, report_dir, logger, config=None):
        self.driver = driver
        self.locator = locator # This is now a Locator object
        self.report_dir = report_dir
        self.logger = logger
        self.config = config or {}
        self.healing_report = {}

    def collect_artifacts(self, exception):
        self.logger.info(f"Starting artifact collection for locator: {self.locator.name}")
        run_id = time.strftime("%Y%m%d-%H%M%S")
        artifact_path = os.path.join(self.report_dir, "self_healing", run_id)
        os.makedirs(artifact_path, exist_ok=True)
        dom_path = os.path.join(artifact_path, "dom.html")
        try:
            with open(dom_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except Exception as e:
            self.logger.error(f"Failed to save DOM: {e}")
            dom_path = None
        screenshot_path = os.path.join(artifact_path, "screenshot.png")
        try:
            self.driver.save_screenshot(screenshot_path)
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            screenshot_path = None
        self.healing_report = {
            "timestamp": time.time(),
            "locator_name": self.locator.name,
            "original_locator": self.locator.value,
            "exception": type(exception).__name__,
            "url": self.driver.current_url,
            "artifacts": {"dom": dom_path, "screenshot": screenshot_path}
        }
        self.logger.info(f"Artifacts collected at: {artifact_path}")
        return self.healing_report

    def save_report(self):
        """Saves the final healing report to a JSON file."""
        report_path = os.path.join(self.report_dir, "self_healing")
        os.makedirs(report_path, exist_ok=True)
        report_file = os.path.join(report_path, "healing_report.json")

        # Append to the report file
        all_reports = []
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                try:
                    all_reports = json.load(f)
                except json.JSONDecodeError:
                    pass # File is empty or corrupt
        all_reports.append(self.healing_report)

        with open(report_file, 'w') as f:
            json.dump(all_reports, f, indent=2)
        self.logger.info(f"Healing report saved to {report_file}")

    def attempt_healing(self, exception):
        self.logger.warning(f"AI Self-healing triggered for locator: {self.locator.name} due to {type(exception).__name__}")

        report = self.collect_artifacts(exception)
        dom_path = report.get("artifacts", {}).get("dom")

        if not dom_path: return None

        with open(dom_path, "r", encoding="utf-8") as f:
            dom_content = f.read()

        preferences = self.config.get("selector_preferences", [])
        ai_result = get_ai_suggestion(dom_content, self.locator.value, type(exception).__name__, preferences)

        if not ai_result or not ai_result.get("candidates"):
            self.logger.error("AI analysis did not return any candidate locators.")
            self.save_report()
            return None

        self.logger.info(f"AI analysis complete. Received {len(ai_result['candidates'])} candidates. Attempting validation...")
        self.healing_report['ai_suggestions'] = ai_result['candidates']

        for candidate in sorted(ai_result['candidates'], key=lambda x: x['confidence'], reverse=True):
            new_locator_tuple = tuple(candidate['locator'])
            try:
                element = self.driver.find_element(new_locator_tuple[0], new_locator_tuple[1])
                self.logger.info(f"Validation successful! Found element with locator: {new_locator_tuple}")

                self.healing_report.update({
                    'healed': True,
                    'healed_with': new_locator_tuple,
                    'confidence': candidate['confidence']
                })

                # --- AUTO-FIX LOGIC ---
                if self.config.get("mode") == "auto":
                    self.logger.info(f"Auto-fixing code for locator '{self.locator.name}'...")
                    fix_successful = rewrite_locator_file(
                        self.locator.file_path,
                        self.locator.name,
                        new_locator_tuple
                    )
                    if fix_successful:
                        self.logger.info(f"Successfully updated {os.path.basename(self.locator.file_path)}.")
                        self.healing_report['auto_fix_status'] = 'Success'
                    else:
                        self.logger.error("Auto-fix failed. Could not rewrite the file.")
                        self.healing_report['auto_fix_status'] = 'Failed'
                else:
                    self.logger.warning("Self-healing mode is 'manual'. Code was not modified. Please update it with the suggestion above.")
                    self.healing_report['auto_fix_status'] = 'Manual'

                self.save_report()
                return element
            except Exception:
                self.logger.warning(f"Candidate {new_locator_tuple} failed validation.")

        self.logger.error("All AI candidate locators failed validation.")
        self.healing_report['healed'] = False
        self.save_report()
        return None