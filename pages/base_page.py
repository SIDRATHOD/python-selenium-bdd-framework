import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from utils.healing import record_failure, attempt_self_heal

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
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable(locator)
            ).click()
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            record_failure(self.driver, self.logger, self.report_dir, action="click", locator=locator, exception=e)
            healed = attempt_self_heal(self.driver, self.logger, self.report_dir, action="click", locator=locator, action_kwargs=None, settings=None)
            if healed:
                return
            raise

    def custom_send_keys(self, locator, text):
        self.logger.info(f"Typing into element: {locator} -> {text}")
        try:
            elem = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(locator)
            )
            elem.clear()
            elem.send_keys(text)
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            record_failure(self.driver, self.logger, self.report_dir, action="send_keys", locator=locator, exception=e)
            healed = attempt_self_heal(self.driver, self.logger, self.report_dir, action="send_keys", locator=locator, action_kwargs={"text": text}, settings=None)
            if healed:
                return
            raise

    def get_text(self, locator):
        self.logger.info(f"Fetching text from element: {locator}")
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(locator)
            ).text
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            record_failure(self.driver, self.logger, self.report_dir, action="get_text", locator=locator, exception=e)
            healed = attempt_self_heal(self.driver, self.logger, self.report_dir, action="get_text", locator=locator, action_kwargs=None, settings=None)
            if healed:
                return ""
            raise

    def take_screenshot(self, name="screenshot"):
        os.makedirs(os.path.join(self.report_dir, "screenshots"), exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = os.path.join(self.report_dir, "screenshots", f"{name}_{timestamp}.png")
        self.driver.save_screenshot(file_path)
        self.logger.error(f"Screenshot captured: {file_path}")
        return file_path
