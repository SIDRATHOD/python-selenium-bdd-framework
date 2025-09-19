from selenium import webdriver
from utils.config_loader import load_config
from utils.logger import get_logger, setup_report_dir
from pages.base_page import BasePage
from utils.page_factory import PageFactory
import os


def before_all(context):
    """
    Called once before all tests are run.

    Loads the configuration data from the config file, sets up the reporting
    directory, and sets up the logger.
    """

    context.config_data = load_config()

    # Setup reporting dir
    context.report_dir = setup_report_dir()
    context.logger = get_logger(context.report_dir)
    context.logger.info(f"===== Starting Test Suite  =====")

def before_scenario(context, scenario):
    """
    Called before each scenario is run.

    Starts the browser, creates the PageFactory object, and logs the start of the scenario.
    """
    context.driver = webdriver.Chrome()
    context.driver.maximize_window()
    context.pages = PageFactory(context.driver, context.logger, context.report_dir)
    context.logger.info(f"===== Starting scenario: {scenario.name} =====")

def after_step(context, step):
    """
    Called after each step is run.

    If the step has failed, takes a screenshot with the name of the step, logs an error with the step name,
    and logs a message indicating that the step failed. Otherwise, logs a message indicating that the step
    passed.
    """
    if step.status == "failed":
        base = BasePage(context.driver, logger=context.logger, report_dir=context.report_dir)
        base.take_screenshot(name=step.name.replace(" ", "_"))
        context.logger.error(f"Step failed: {step.name}")
    else:
        context.logger.info(f"Step passed: {step.name}")

def after_scenario(context, scenario):
    """
    Called after each scenario is run.

    If the driver has been created, quits the driver and logs the finish of the scenario.
    """
    if hasattr(context, "driver"):
        context.driver.quit()
    context.logger.info(f"===== Finished scenario: {scenario.name} =====")

def after_all(context):
    """
    Called after all tests are run.

    Logs the finish of the test suite and the locations of the log file and screenshot directory.
    """
    context.logger.info("===== Test Suite Finished =====")
    log_file = os.path.join(context.report_dir, "test.log")
    screenshot_dir = os.path.join(context.report_dir, "screenshots")

    context.logger.info("\nTest run completed!")
    context.logger.info(f"Logs: {os.path.abspath(log_file)}")
    context.logger.info(f"Screenshots: {os.path.abspath(screenshot_dir)}\n")
