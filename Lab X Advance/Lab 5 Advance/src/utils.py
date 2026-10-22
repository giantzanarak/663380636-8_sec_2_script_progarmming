# agentic-comm-automator/src/utils.py
import logging
import os
import datetime

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from the project's .env file (if it exists)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_logging(name, level=logging.INFO):
    """Sets up a logger for specific modules."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers: # Prevent adding multiple handlers if called multiple times
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    # Don't also pass records up to the root logger (avoids every line printing twice)
    logger.propagate = False
    return logger

def get_env_variable(var_name, default=None):
    """Retrieves an environment variable, raising an error if it is not set and has no default."""
    value = os.getenv(var_name)
    if value in (None, ""):
        if default is not None:
            return default
        raise ValueError(f"Environment variable '{var_name}' not set. Please check your .env file or environment settings.")
    return value

def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    if not path:
        return
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating directory {path}: {e}")
        raise

def log_audit_entry(audit_log_list, status, message, task_type="N/A", details=None):
    """Adds an entry to the audit log list."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "task_type": task_type,
        "message": message,
        "details": details if details else {}
    }
    audit_log_list.append(log_entry)
    if status in ("ERROR", "CRITICAL"):
        logging.error(f"AUDIT LOG - {status}: {message} | Task: {task_type} | Details: {details}")
    elif status == "WARNING":
        logging.warning(f"AUDIT LOG - {status}: {message} | Task: {task_type}")
    else:
        logging.info(f"AUDIT LOG - {status}: {message} | Task: {task_type}")
