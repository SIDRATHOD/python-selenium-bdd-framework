import logging
import os
import time

def setup_report_dir():
    """Sets up a directory for test reports, with a timestamped subdirectory
    and a 'screenshots' subdirectory for saving screenshot images."""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    report_dir = os.path.join("reports", timestamp)
    os.makedirs(os.path.join(report_dir, "screenshots"), exist_ok=True)
    return report_dir

def get_logger(report_dir, name="test_logger"):
    """Returns a logger that logs to a file and the console.

    The logger's name is the given name, or "test_logger" if no name is given.
    The logger will write to a file in the given report directory, and to the
    console. The file logger will write at DEBUG level, while the console logger
    will write at INFO level.

    The log file is named "test.log" and is placed in the report directory.

    The logger is configured with a formatter that writes logs in the format:

        %(asctime)s - %(levelname)s - %(message)s

    The logger is only configured if it has not already been configured.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    log_file = os.path.join(report_dir, "test.log")

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
