from pages.base_page import BasePage
from locator.profile_locators import ProfileLocators

class ProfilePage(BasePage):
    def __init__(self, driver, logger=None, report_dir="reports"):
        """
        Constructor

        :param driver: Instance of WebDriver
        :param logger: Logger object
        :param report_dir: Directory path to store reports
        """
        super().__init__(driver, logger=logger, report_dir=report_dir)

    def upload_profile_picture(self, file_path):
        self.custom_send_keys(ProfileLocators.FILE_INPUT, file_path)
        self.click(ProfileLocators.UPLOAD_BUTTON)

    def get_upload_message(self):
        """
        Retrieves the upload message after attempting to upload a profile picture.

        :return: The text message after attempting to upload a profile picture
        """
        return self.get_text(ProfileLocators.UPLOAD_MSG)
