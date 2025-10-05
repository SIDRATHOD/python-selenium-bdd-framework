import os
import time
import logging
from selenium.webdriver.common.by import By
from utils.ai_provider import get_ai_suggestion

# Configure a logger for the healer
logger = logging.getLogger(__name__)

class Healer:
    def __init__(self, driver, locator, report_dir, logger, config=None):
        self.driver = driver
        self.locator = locator
        self.report_dir = report_dir
        self.logger = logger
        self.config = config or {}
        self.healing_report = {}

    def collect_artifacts(self, exception):
        # ... (This method remains unchanged)
        self.logger.info(f"Starting artifact collection for locator: {self.locator}")
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
            "locator": str(self.locator),
            "exception": type(exception).__name__,
            "url": self.driver.current_url,
            "artifacts": {"dom": dom_path, "screenshot": screenshot_path}
        }
        self.logger.info(f"Artifacts collected at: {artifact_path}")
        return self.healing_report

    def attempt_healing(self, exception):
        """
        Main entry point for the healing process.
        """
        self.logger.warning(f"AI Self-healing triggered for locator: {self.locator} due to {type(exception).__name__}")

        report = self.collect_artifacts(exception)
        dom_path = report.get("artifacts", {}).get("dom")

        if not dom_path or not os.path.exists(dom_path):
            self.logger.error("DOM snapshot not found. Cannot proceed with AI analysis.")
            return None

        with open(dom_path, "r", encoding="utf-8") as f:
            dom_content = f.read()

        preferences = self.config.get("selector_preferences", [])
        ai_result = get_ai_suggestion(dom_content, self.locator, type(exception).__name__, preferences)

        if not ai_result or not ai_result.get("candidates"):
            self.logger.error("AI analysis did not return any candidate locators.")
            return None

        self.logger.info(f"AI analysis complete. Received {len(ai_result['candidates'])} candidates. Attempting validation...")
        self.healing_report['ai_suggestions'] = ai_result['candidates']

        # --- NEW: Validation Loop ---
        for candidate in sorted(ai_result['candidates'], key=lambda x: x['confidence'], reverse=True):
            new_locator_tuple = tuple(candidate['locator'])
            self.logger.info(f"Validating candidate: {new_locator_tuple} (Confidence: {candidate['confidence']})")
            try:
                # Use a simple find_element to check if the locator is valid
                element = self.driver.find_element(new_locator_tuple[0], new_locator_tuple[1])
                self.logger.info(f"Validation successful! Found element with locator: {new_locator_tuple}")

                # Add healing info to the report
                self.healing_report['healed'] = True
                self.healing_report['healed_with'] = new_locator_tuple
                self.healing_report['original_locator'] = self.locator

                # In the final phase, we will also write this report to a file.

                return element # Return the healed element to proceed with the test
            except Exception:
                self.logger.warning(f"Candidate {new_locator_tuple} failed validation.")

        self.logger.error("All AI candidate locators failed validation.")
        self.healing_report['healed'] = False
        return None # Return None if no candidates worked