from behave import given
from pages.auth_page import AuthPage
from pages.profile_page import ProfilePage
import time

@given("the user is logged in")
def step_impl(context):
    """
    Ensure the user is logged in.

    This step is a given, so it should not fail the test if the user is not logged in.
    Instead, it will log in the user if they are not logged in.

    :param context: The behave context.
    """
    context.driver.get(context.config_data["base_url"])

    auth_page = context.pages.get_auth_page()

    # Signup (if not already exists)
    try:
        auth_page.signup(context.config_data["username"], context.config_data["password"])
        time.sleep(1)
        context.driver.switch_to.alert.accept()
    except Exception:
        context.logger.info("User may already exist, skipping signup")

    # Login
    auth_page.login(context.config_data["username"], context.config_data["password"])

    context.logger.info(f"Logged in as {context.config_data['username']}")
