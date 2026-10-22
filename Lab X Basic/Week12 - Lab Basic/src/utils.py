"""
email-sms-automator/src/utils.py
Utility functions for logging, environment variables and directories.
"""

import logging
import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load variables from the project's .env file (works from any working directory)
load_dotenv(os.path.join(BASE_DIR, ".env"))


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Returns a logger with one console handler (no duplicate handlers or double printing)."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging(__name__)


def get_env_variable(var_name: str, default: str = None) -> str:
    """
    Returns an environment variable.

    :raises ValueError: if it is missing/empty and no default is given.
    """
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{var_name}' not set. Please check your .env file.")
    return value.strip()


def ensure_directory_exists(path: str) -> None:
    """Creates a directory (and parents) if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise
