import os
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.config_loader import load_healing_config
from utils.healer import Healer
# Make sure to import the Locator object if it's not already
from utils.locator import Locator

class BasePage:
    # ... (__init__ remains the same)
    def __init__(self, driver, timeout=10, logger=None, report_dir="reports"):
        self.driver = driver
        self.timeout = timeout
        self.logger = logger
        self.report_dir = report_dir
        self.healing_config = load_healing_config().get("self_healing", {})

    def _find_element(self, locator: Locator, condition):
        """
        Private method to find an element with self-healing capabilities.
        Now expects a Locator object.
        """
        try:
            # Use locator.value to get the actual tuple for Selenium
            element = WebDriverWait(self.driver, self.timeout).until(condition(locator.value))
            return element
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            self.logger.error(f"Element with locator '{locator.name}' not found. Exception: {e.__class__.__name__}")

            if self.healing_config.get("enabled", False):
                # Pass the full Locator object to the Healer
                healer = Healer(self.driver, locator, self.report_dir, self.logger, config=self.healing_config)
                healed_element = healer.attempt_healing(e)

                if healed_element:
                    self.logger.info("Self-healing successful! Test will proceed with the new element.")
                    return healed_element

            self.take_screenshot(f"element_not_found_{locator.name}")
            raise e

    def click(self, locator: Locator):
        self.logger.info(f"Clicking element: {locator.name}")
        element = self._find_element(locator, EC.element_to_be_clickable)
        element.click()

    def custom_send_keys(self, locator: Locator, text):
        self.logger.info(f"Typing into element: {locator.name} -> {text}")
        elem = self._find_element(locator, EC.presence_of_element_located)
        elem.clear()
        elem.send_keys(text)

    def get_text(self, locator: Locator):
        self.logger.info(f"Fetching text from element: {locator.name}")
        element = self._find_element(locator, EC.presence_of_element_located)
        return element.text

    # ... (take_screenshot remains the same)
    def take_screenshot(self, name="screenshot"):
        screenshots_dir = os.path.join(self.report_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
        file_name = f"{safe_name}_{timestamp}.png"
        file_path = os.path.join(screenshots_dir, file_name)
        try:
            self.driver.save_screenshot(file_path)
            self.logger.error(f"Screenshot captured: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
        return file_path