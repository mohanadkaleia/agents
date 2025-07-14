import logging
import os
import sys
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s: [%(levelname)s] [%(name)s] %(message)s")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "..", "agents.log")


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(FORMATTER)
        return file_handler
    except PermissionError:
        print("Permission denied to write to the log file.")
        return None


def get_logger(logger_name, level=logging.DEBUG):
    logger = logging.getLogger(logger_name)

    # better to have too much log than not enough
    logger.setLevel(level)

    logger.addHandler(get_console_handler())
    file_handler = get_file_handler()
    if file_handler:
        logger.addHandler(file_handler)

    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False

    return logger