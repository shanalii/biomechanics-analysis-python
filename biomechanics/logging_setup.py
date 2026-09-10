"""Logging configuration shared by the analysis entry-point script."""

import glob
import logging
import os
from datetime import datetime

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
LOG_FILE_PATTERN = "output_*.txt"
MAX_OUTPUT_FILES = 10


def timestamped_log_path(output_dir: str, prefix: str = "output") -> str:
    """Returns a path like output_dir/output_20260910_170512.txt."""
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    return os.path.join(output_dir, f"{prefix}_{timestamp}.txt")


def prune_old_logs(output_dir: str, max_files: int = MAX_OUTPUT_FILES) -> None:
    """Deletes the oldest log file(s) in output_dir until fewer than max_files remain.

    Called before writing a new log file, so the directory holds at most
    max_files once the new one is written.
    """
    log_files = sorted(
        glob.glob(os.path.join(output_dir, LOG_FILE_PATTERN)),
        key=os.path.getmtime,
    )
    while len(log_files) >= max_files:
        oldest = log_files.pop(0)
        os.remove(oldest)


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
