# agentic-spreadsheet-processor/src/config_parser.py
import json
import os
from .utils import setup_logging

logger = setup_logging(__name__)

class ConfigParser:
    """
    Parses and validates the spreadsheet automation configuration from a JSON file.
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
        required_top_level_fields = ["input_file", "output_file", "tasks"]
        for field in required_top_level_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field in config: '{field}'")

        if not isinstance(self.config["tasks"], list):
            raise ValueError("Config field 'tasks' must be a list.")

        # Basic validation for each task
        for i, task in enumerate(self.config["tasks"]):
            task_type = task.get("type")
            if task_type is None:
                raise ValueError(f"Task {i} is missing 'type' field.")

            # copy_data works with source_sheet/dest_sheet instead of a single 'sheet'
            if task_type == "copy_data":
                if "source_sheet" not in task or "dest_sheet" not in task:
                    raise ValueError(f"copy_data task {i} requires 'source_sheet' and 'dest_sheet'.")
                continue

            if "sheet" not in task:
                raise ValueError(f"Task {i} (type: {task_type}) is missing 'sheet' field.")

            if task_type == "calculate_column":
                if "target_column" not in task or "formula" not in task:
                    raise ValueError(f"calculate_column task {i} requires 'target_column' and 'formula'.")

            if task_type == "chart":
                if "chart_type" not in task or "data_range" not in task:
                    raise ValueError(f"Chart task {i} requires 'chart_type' and 'data_range'.")

            if task_type == "conditional_format":
                if "range" not in task or "rule_type" not in task:
                    raise ValueError(f"Conditional format task {i} requires 'range' and 'rule_type'.")

            if task_type == "summary":
                if "metrics" not in task or not isinstance(task["metrics"], list):
                    raise ValueError(f"Summary task {i} requires a 'metrics' list.")

        logger.info("Configuration validated.")
