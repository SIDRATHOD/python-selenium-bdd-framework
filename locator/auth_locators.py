from selenium.webdriver.common.by import By
from utils.locator import Locator
import os

# Get the absolute path of the current file to pass to the Locator object
file_path = os.path.abspath(__file__)

class AuthLocators:
    SIGNUP_USERNAME = Locator((By.ID, "signup-username"), "SIGNUP_USERNAME", file_path)
    SIGNUP_PASSWORD = Locator((By.ID, "signup-password"), "SIGNUP_PASSWORD", file_path)
    SIGNUP_BUTTON = Locator((By.XPATH, "//button[text()='Sign Up']"), "SIGNUP_BUTTON", file_path)

    LOGIN_USERNAME = Locator((By.ID, "login-username"), "LOGIN_USERNAME", file_path)
    LOGIN_PASSWORD = Locator((By.ID, "login-password"), "LOGIN_PASSWORD", file_path)
    LOGIN_BUTTON = Locator((By.XPATH, "//button[text()='Login']"), "LOGIN_BUTTON", file_path)