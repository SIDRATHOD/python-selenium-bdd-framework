from pages.base_page import BasePage
from locator.auth_locators import AuthLocators

class AuthPage(BasePage):
    def __init__(self, driver, logger=None, report_dir="reports"):
        """
        Constructor

        :param driver: Instance of WebDriver
        :param logger: Logger object
        :param report_dir: Directory path to store reports
        """
        super().__init__(driver, logger=logger, report_dir=report_dir)

    def signup(self, username, password):
        self.custom_send_keys(AuthLocators.SIGNUP_USERNAME, username)
        self.custom_send_keys(AuthLocators.SIGNUP_PASSWORD, password)
        self.click(AuthLocators.SIGNUP_BUTTON)

    def login(self, username, password):
        self.custom_send_keys(AuthLocators.LOGIN_USERNAME, username)
        self.custom_send_keys(AuthLocators.LOGIN_PASSWORD, password)
        self.click(AuthLocators.LOGIN_BUTTON)
