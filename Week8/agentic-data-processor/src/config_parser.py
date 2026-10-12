# agentic-data-processor/src/config_parser.py
import json
import os
from .utils import setup_logging

logger = setup_logging(__name__)

class ConfigParser:
    """
    Parses and validates the data automation configuration from a JSON file.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}

    def load_config(self):
        """Loads the configuration from the specified JSON file."""
        if not os.path.exists(self.config_path):
            logger.critical(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format in config file: {e}")
            raise ValueError(f"Invalid JSON format in config file: {e}")

        self._validate_config()
        logger.info(f"Configuration loaded successfully from {self.config_path}")
        return self.config

    def _validate_config(self):
        """
        Validates the loaded configuration to ensure required fields and task structures are present.
        This validation can be extended based on all possible task types.
        """
        required_top_level_fields = ["tasks"]
        for field in required_top_level_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field in config: '{field}'")

        if not isinstance(self.config["tasks"], list):
            raise ValueError("Config field 'tasks' must be a list.")

        # Basic validation for each task
        for i, task in enumerate(self.config["tasks"]):
            if "type" not in task:
                raise ValueError(f"Task {i} is missing 'type' field.")

            # save_csv / save_json only write a file, so they don't produce data for the store
            if task["type"] not in ["save_csv", "save_json"] and "output_data_key" not in task:
                raise ValueError(f"Task {i} (type: {task['type']}) is missing 'output_data_key' field.")

            # Specific validations per task type
            if task["type"] in ["load_csv", "load_json", "save_csv", "save_json"]:
                if "file_path" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'file_path'.")

            if task["type"] in ["save_csv", "save_json"]:
                if "input_data_key" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'input_data_key'.")

            if task["type"] == "save_csv" and "fieldnames" not in task:
                logger.warning(f"Task {i} (save_csv) has no explicit 'fieldnames'. Will attempt to derive from data.")

            if task["type"] in ["transform_csv_aggregate", "filter_csv", "update_json_data",
                                "query_json_data", "csv_to_json_conversion", "json_to_csv_conversion"]:
                if "input_data_key" not in task:
                    raise ValueError(f"Task {i} (type: {task['type']}) requires 'input_data_key'.")

        logger.info("Configuration validated.")
