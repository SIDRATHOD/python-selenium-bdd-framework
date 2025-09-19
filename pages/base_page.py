import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def click(self, locator):
        self.logger.info(f"Clicking element: {locator}")
        WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable(locator)
        ).click()

    def custom_send_keys(self, locator, text):
        self.logger.info(f"Typing into element: {locator} -> {text}")
        elem = WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(locator)
        )
        elem.clear()
        elem.send_keys(text)

    def get_text(self, locator):
        self.logger.info(f"Fetching text from element: {locator}")
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(locator)
        ).text

    def take_screenshot(self, name="screenshot"):
        os.makedirs(os.path.join(self.report_dir, "screenshots"), exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = os.path.join(self.report_dir, "screenshots", f"{name}_{timestamp}.png")
        self.driver.save_screenshot(file_path)
        self.logger.error(f"Screenshot captured: {file_path}")
        return file_path
