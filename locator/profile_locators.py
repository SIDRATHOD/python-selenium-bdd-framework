from selenium.webdriver.common.by import By

class ProfileLocators:
    FILE_INPUT = (By.ID, "profile-pic")
    UPLOAD_BUTTON = (By.XPATH, "//button[@onclick='uploadProfilePic()']")
    UPLOAD_MSG = (By.ID, "upload-msg")
