# agentic-comm-automator/src/config_parser.py
import json
import os
import re

from .utils import setup_logging

logger = setup_logging(__name__)

# ${ENV_VAR} placeholders in the config are replaced with environment variables (from .env)
ENV_PATTERN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")

class ConfigParser:
    """Parses and validates the communication automation configuration from a JSON file."""
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}

    def load_config(self):
        """Loads the configuration, substitutes ${ENV_VAR} values and validates it."""
        if not os.path.exists(self.config_path):
            logger.critical(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format in config file: {e}")
            raise ValueError(f"Invalid JSON format in config file: {e}")

        self.config = self._substitute_env(self.config)
        self._validate_config()
        logger.info(f"Configuration loaded successfully from {self.config_path}")
        return self.config

    def _substitute_env(self, value):
        """Recursively replaces ${ENV_VAR} in strings. Unknown variables are reported as errors."""
        if isinstance(value, dict):
            return {k: self._substitute_env(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._substitute_env(v) for v in value]
        if isinstance(value, str):
            def replace(match):
                name = match.group(1)
                if name not in os.environ:
                    raise ValueError(f"Config uses ${{{name}}} but '{name}' is not set in .env")
                return os.environ[name]
            return ENV_PATTERN.sub(replace, value)
        return value

    def _validate_config(self):
        if not isinstance(self.config.get("tasks"), list):
            raise ValueError("Config must contain a 'tasks' list.")

        for i, task in enumerate(self.config["tasks"]):
            task_type = task.get("type")
            if task_type is None:
                raise ValueError(f"Task {i} is missing 'type' field.")
            if "name" not in task:
                raise ValueError(f"Task {i} (type: {task_type}) is missing 'name' field.")
            params = task.get("parameters", {})

            if task_type == "send_email":
                missing = [k for k in ["recipients", "subject_template", "body_template"] if k not in params]
                if missing:
                    raise ValueError(f"Task {i} (send_email) is missing parameters: {missing}")
                if not isinstance(params["recipients"], dict) or not params["recipients"].get("to"):
                    raise ValueError(f"Task {i} (send_email) 'recipients' must be a dict with a non-empty 'to' list.")
            elif task_type == "send_sms":
                missing = [k for k in ["phone_numbers", "message_template"] if k not in params]
                if missing:
                    raise ValueError(f"Task {i} (send_sms) is missing parameters: {missing}")
            elif task_type == "process_inbox":
                if "search_criteria" not in params:
                    raise ValueError(f"Task {i} (process_inbox) requires 'search_criteria' in parameters.")
                for j, rule in enumerate(params.get("rules", [])):
                    if "if" not in rule or "then" not in rule:
                        raise ValueError(f"Task {i} (process_inbox) rule {j} needs both 'if' and 'then'.")
            else:
                logger.warning(f"Task {i} has unknown type '{task_type}'. It will be skipped.")

        logger.info("Configuration validated.")
