import os
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# AI Healer Imports
from utils.config_loader import load_healing_config
from utils.healer import Healer

class BasePage:
    def __init__(self, driver, timeout=10, logger=None, report_dir="reports"):
        """
        Constructor

        :param driver: Instance of WebDriver
        :param timeout: Timeout in seconds to wait for an element
        :param logger: Logger object
        :param report_dir: Directory path to store reports
        """
        self.driver = driver
        self.timeout = timeout
        self.logger = logger
        self.report_dir = report_dir
        self.healing_config = load_healing_config().get("self_healing", {})

    def _find_element(self, locator, condition):
        """
        Private method to find an element with self-healing capabilities.
        """
        try:
            element = WebDriverWait(self.driver, self.timeout).until(condition(locator))
            return element
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            self.logger.error(f"Element with locator '{locator}' not found. Exception: {e.__class__.__name__}")

            if self.healing_config.get("enabled", False):
                # Pass the configuration to the Healer
                healer = Healer(self.driver, locator, self.report_dir, self.logger, config=self.healing_config)
                healed_element = healer.attempt_healing(e)

                if healed_element:
                    self.logger.info("Self-healing successful! Test will proceed with the new element.")
                    return healed_element

            # If healing is disabled or failed, take a screenshot and re-raise the original exception
            self.take_screenshot(f"element_not_found_{locator[1]}")
            raise e

    def click(self, locator):
        self.logger.info(f"Clicking element: {locator}")
        element = self._find_element(locator, EC.element_to_be_clickable)
        element.click()

    def custom_send_keys(self, locator, text):
        self.logger.info(f"Typing into element: {locator} -> {text}")
        elem = self._find_element(locator, EC.presence_of_element_located)
        elem.clear()
        elem.send_keys(text)

    def get_text(self, locator):
        self.logger.info(f"Fetching text from element: {locator}")
        element = self._find_element(locator, EC.presence_of_element_located)
        return element.text

    def take_screenshot(self, name="screenshot"):
        # Ensure the directory for screenshots within the report_dir exists
        screenshots_dir = os.path.join(self.report_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        # Sanitize filename to be safe for all filesystems
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
        file_name = f"{safe_name}_{timestamp}.png"
        file_path = os.path.join(screenshots_dir, file_name)

        try:
            self.driver.save_screenshot(file_path)
            self.logger.error(f"Screenshot captured: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")

        return file_path