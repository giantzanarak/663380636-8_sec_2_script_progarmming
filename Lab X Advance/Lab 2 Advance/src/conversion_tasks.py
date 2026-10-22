# agentic-data-processor/src/conversion_tasks.py
import json
from .utils import setup_logging

logger = setup_logging(__name__)

class ConversionTasks:
    """
    Handles conversions between CSV (list of dicts) and JSON formats.
    """
    def __init__(self):
        logger.info("ConversionTasks initialized.")

    @staticmethod
    def _convert_value(value):
        """Converts a CSV string into int, float, bool or None where possible."""
        if value is None:
            return None
        text = value.strip()
        if text == '' or text.lower() == 'null':
            return None
        if text.lower() in ['true', 'false']:
            return text.lower() == 'true'
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            return text

    def csv_to_json(self, csv_data):
        """
        Converts CSV data (list of dictionaries) to JSON-compatible Python list of dicts.
        Numeric strings are converted to actual numbers.
        """
        if not csv_data:
            logger.warning("No CSV data to convert to JSON.")
            return []

        json_data = [{key: self._convert_value(value) for key, value in row.items()} for row in csv_data]

        logger.info(f"Converted {len(csv_data)} CSV rows to JSON format.")
        return json_data

    def json_to_csv(self, json_data, fieldnames=None):
        """
        Converts JSON data (list of dictionaries) to a CSV-compatible list of dictionaries.
        Assumes flat JSON objects or flattens simple nested keys (e.g. details.brand).
        """
        if not json_data:
            logger.warning("No JSON data to convert to CSV.")
            return [], []

        # If fieldnames not provided, collect all unique keys, including from nested dicts like 'details'
        if fieldnames is None:
            all_keys = set()
            for item in json_data:
                for k, v in item.items():
                    if isinstance(v, dict):
                        for sub_k in v.keys():
                            all_keys.add(f"{k}.{sub_k}") # e.g., 'details.brand'
                    else:
                        all_keys.add(k)
            fieldnames = sorted(all_keys)
            logger.info(f"Inferred fieldnames for JSON to CSV: {fieldnames}")

        csv_rows = []
        for item in json_data:
            row = {}
            for field in fieldnames:
                if '.' in field: # Handle simple nested keys
                    parent_key, child_key = field.split('.', 1)
                    parent_value = item.get(parent_key)
                    value = parent_value.get(child_key, '') if isinstance(parent_value, dict) else ''
                else:
                    value = item.get(field, '')
                # Convert complex types (lists, dicts) to a JSON string representation
                row[field] = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            csv_rows.append(row)

        logger.info(f"Converted {len(json_data)} JSON objects to CSV format.")
        return csv_rows, fieldnames
