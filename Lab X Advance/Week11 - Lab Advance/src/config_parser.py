# agentic-document-automator/src/config_parser.py
import json
import os
from .utils import setup_logging

logger = setup_logging(__name__)

# Fields each task type needs in the config
REQUIRED_TASK_FIELDS = {
    "generate_word_report": ["template_path", "output_path"],
    "apply_pdf_watermark": ["input_pdf", "output_pdf", "watermark_text"],
    "merge_pdfs": ["input_pdfs", "output_pdf"],
    "extract_word_text": ["input_docx", "output_text_file"],
    "extract_pdf_text": ["input_pdf", "output_text_file"],
}

class ConfigParser:
    """Parses and validates the document automation configuration from a JSON file."""
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
        """Validates required top-level fields and the fields each task type needs."""
        for field in ["global_data", "tasks"]:
            if field not in self.config:
                raise ValueError(f"Missing required field in config: '{field}'")
        if not isinstance(self.config["tasks"], list):
            raise ValueError("Config field 'tasks' must be a list.")

        for i, task in enumerate(self.config["tasks"]):
            task_type = task.get("type")
            if task_type is None:
                raise ValueError(f"Task {i} is missing 'type' field.")
            if task_type not in REQUIRED_TASK_FIELDS:
                logger.warning(f"Task {i} has unknown type '{task_type}'. It will be skipped.")
                continue
            missing = [field for field in REQUIRED_TASK_FIELDS[task_type] if field not in task]
            if missing:
                raise ValueError(f"Task {i} (type: {task_type}) is missing required field(s): {missing}")
            if task_type == "merge_pdfs" and not isinstance(task["input_pdfs"], list):
                raise ValueError(f"Task {i} (merge_pdfs): 'input_pdfs' must be a list.")
        logger.info("Configuration validated.")
