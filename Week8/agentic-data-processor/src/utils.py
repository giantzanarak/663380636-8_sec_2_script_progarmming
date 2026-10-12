# agentic-data-processor/src/utils.py
import logging
import os
import json
import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_logging(name, level=logging.INFO, log_file=None):
    """Sets up a logger for specific modules, allowing file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Ensure handlers are added only once per logger instance
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler (optional)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    # Don't also pass records up to the root logger (avoids every line printing twice)
    logger.propagate = False
    return logger

def ensure_directory_exists(path):
    """Ensures that a directory exists, creating it if necessary."""
    if not path:
        return
    try:
        os.makedirs(path, exist_ok=True)
        logging.info(f"Directory ensured: {path}")
    except OSError as e:
        logging.error(f"Error creating directory {path}: {e}")
        raise

def log_audit_entry(audit_log_list, status, message, task_type="N/A", details=None):
    """Adds an entry to the audit log list."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status,
        "task_type": task_type,
        "message": message,
        "details": details if details else {}
    }
    audit_log_list.append(log_entry)
    if status == "ERROR" or status == "CRITICAL":
        logging.error(f"AUDIT LOG - {status}: {message} | Task: {task_type} | Details: {details}")
    else:
        logging.info(f"AUDIT LOG - {status}: {message} | Task: {task_type}")
