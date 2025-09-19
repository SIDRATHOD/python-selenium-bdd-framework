from selenium.webdriver.common.by import By

class AuthLocators:
    SIGNUP_USERNAME = (By.ID, "signup-username")
    SIGNUP_PASSWORD = (By.ID, "signup-password")
    SIGNUP_BUTTON = (By.XPATH, "//button[text()='Sign Up']")

    LOGIN_USERNAME = (By.ID, "login-username")
    LOGIN_PASSWORD = (By.ID, "login-password")
    LOGIN_BUTTON = (By.XPATH, "//button[text()='Login']")
