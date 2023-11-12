import logging
import sys
from logging.handlers import RotatingFileHandler

from core.config import config


def init_logger():
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)

    file_error_handler = RotatingFileHandler(
        "./logs/errors.log",
        maxBytes=5000000,
        backupCount=5,
    )
    file_error_handler.setLevel(logging.ERROR)

    file_warning_handler = RotatingFileHandler(
        "./logs/warnings.log",
        maxBytes=5000000,
        backupCount=5,
    )
    file_warning_handler.setLevel(logging.WARNING)

    file_info_handler = RotatingFileHandler(
        "./logs/info.log",
        maxBytes=5000000,
        backupCount=5,
    )
    file_info_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            stdout_handler,
            file_error_handler,
            file_info_handler,
        ],
    )

    if config.DEBUG:
        stdout_handler.setLevel(logging.DEBUG)

        file_debug_handler = RotatingFileHandler(
            "./logs/debug.log",
            maxBytes=1000000,
            backupCount=2,
        )
        file_debug_handler.setLevel(logging.DEBUG)

        logging.getLogger().addHandler(file_debug_handler)
