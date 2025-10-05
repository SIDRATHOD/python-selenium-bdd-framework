from selenium.webdriver.common.by import By
from utils.locator import Locator
import os

# Get the absolute path of the current file to pass to the Locator object
file_path = os.path.abspath(__file__)

class ProfileLocators:
    FILE_INPUT = Locator((By.ID, "profile-pic"), "FILE_INPUT", file_path)
    UPLOAD_BUTTON = Locator((By.XPATH, "//button[@onclick='uploadProfilePic()']"), "UPLOAD_BUTTON", file_path)
    UPLOAD_MSG = Locator((By.ID, "upload-msg"), "UPLOAD_MSG", file_path)