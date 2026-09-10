"""Logging configuration shared by the analysis entry-point script."""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"


def configure_logging(log_path: str, level: int = logging.DEBUG) -> logging.Logger:
    """Configure the root logger to log to both a file and the console.

    Clears any handlers left over from a previous run (useful when this is
    re-run in Blender's persistent scripting session).
    """
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(level)

    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
