from pages.auth_page import AuthPage
from pages.profile_page import ProfilePage

class PageFactory:
    def __init__(self, driver, logger, report_dir):
        """
        :param driver: Instance of WebDriver
        :param logger: Logger object
        :param report_dir: Directory path to store reports
        """
        self.driver = driver
        self.logger = logger
        self.report_dir = report_dir

    def get_auth_page(self):
        """
        Returns an instance of AuthPage
        :return: Instance of AuthPage
        """
        return AuthPage(self.driver, logger=self.logger, report_dir=self.report_dir)

    def get_profile_page(self):
        """
        Returns an instance of ProfilePage
        :return: Instance of ProfilePage
        """
        return ProfilePage(self.driver, logger=self.logger, report_dir=self.report_dir)