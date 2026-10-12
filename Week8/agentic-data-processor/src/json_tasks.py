# agentic-data-processor/src/json_tasks.py
import json
import os
from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class JSONTasks:
    """
    Handles advanced reading, writing, and manipulation of JSON data.
    """
    def __init__(self):
        logger.info("JSONTasks initialized.")

    def load_json(self, file_path):
        """Loads a JSON file and returns the Python object."""
        if not os.path.exists(file_path):
            logger.error(f"JSON file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Successfully loaded JSON from '{file_path}'.")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading JSON file '{file_path}': {e}")
            return None

    def save_json(self, data, file_path, indent=2):
        """Saves a Python object to a JSON file, with pretty-printing."""
        if data is None:
            logger.warning("No data provided to save to JSON.")
            return False

        ensure_directory_exists(os.path.dirname(file_path))

        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully saved JSON to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON file '{file_path}': {e}")
            return False

    def _navigate_to_parent(self, data, keys, path):
        """
        Walks `keys[:-1]` from `data` and returns the parent node of the final key,
        or None if the path cannot be followed.
        """
        current_node = data
        for key in keys[:-1]:
            if isinstance(current_node, dict):
                if key not in current_node:
                    logger.warning(f"Path '{path}' not found at key '{key}'.")
                    return None
                current_node = current_node[key]
            elif isinstance(current_node, list) and key.isdigit():
                index = int(key)
                if not 0 <= index < len(current_node):
                    logger.warning(f"Path '{path}' not found: index '{key}' out of bounds for list.")
                    return None
                current_node = current_node[index]
            else:
                logger.warning(f"Path '{path}' not navigable at key '{key}' (cannot use key '{key}' on a {type(current_node).__name__}).")
                return None
        return current_node

    def update_json_data(self, data, updates):
        """
        Applies updates to a JSON-like Python object.
        `updates` is a list of dicts: [{"path": "key1.key2", "value": "new_value", "operation": "set"}, ...]
        Supported operations: 'set', 'add_to_list', 'remove_from_list'.
        An empty path ("") refers to the root object (e.g. to append to a root-level list).
        """
        if not data:
            logger.warning("No JSON data provided for update.")
            return data

        modified_data = json.loads(json.dumps(data)) # Deep copy to avoid modifying original reference

        for update in updates or []:
            path = update.get("path")
            value = update.get("value")
            operation = update.get("operation", "set")

            if path is None:
                logger.warning(f"Update skipped: missing 'path' in update: {update}")
                continue

            try:
                # Empty path: operate on the root object itself
                if path == "":
                    if operation == "add_to_list" and isinstance(modified_data, list):
                        modified_data.append(value)
                        logger.info(f"Added '{value}' to root list.")
                    else:
                        logger.warning(f"Operation '{operation}' is not supported on the root object. Skipping update: {update}")
                    continue

                keys = path.split('.')
                current_node = self._navigate_to_parent(modified_data, keys, path)
                if current_node is None:
                    logger.warning(f"Skipping update: {update}")
                    continue

                target_key = keys[-1]

                if operation == "set":
                    if isinstance(current_node, dict):
                        current_node[target_key] = value
                        logger.info(f"Set '{path}' to '{value}'.")
                    elif isinstance(current_node, list) and target_key.isdigit() and 0 <= int(target_key) < len(current_node):
                        current_node[int(target_key)] = value
                        logger.info(f"Set '{path}' (list index) to '{value}'.")
                    else:
                        logger.warning(f"Cannot 'set' value for path '{path}': target is not a dict key or valid list index. Skipping update: {update}")

                elif operation in ("add_to_list", "remove_from_list"):
                    target_list = current_node.get(target_key) if isinstance(current_node, dict) else None
                    if not isinstance(target_list, list):
                        logger.warning(f"Cannot '{operation}' for path '{path}': target is not a list. Skipping update: {update}")
                    elif operation == "add_to_list":
                        target_list.append(value)
                        logger.info(f"Added '{value}' to list at '{path}'.")
                    elif value in target_list:
                        target_list.remove(value)
                        logger.info(f"Removed '{value}' from list at '{path}'.")
                    else:
                        logger.warning(f"Value '{value}' not found in list at '{path}'. Skipping remove: {update}")

                else:
                    logger.warning(f"Unsupported operation '{operation}' for path '{path}'. Skipping update: {update}")

            except Exception as e:
                logger.error(f"Error applying JSON update for path '{path}': {e}. Update: {update}")

        return modified_data

    def query_json_data(self, data, path):
        """
        Queries a specific element from nested JSON data using a dot-notation path.
        Returns the value or None if not found.
        """
        if not data:
            logger.warning("No JSON data to query.")
            return None

        keys = path.split('.')
        parent = self._navigate_to_parent(data, keys, path)
        if parent is None:
            return None

        last_key = keys[-1]
        if isinstance(parent, dict):
            result = parent.get(last_key)
        elif isinstance(parent, list) and last_key.isdigit() and 0 <= int(last_key) < len(parent):
            result = parent[int(last_key)]
        else:
            logger.warning(f"Query path '{path}' failed at key '{last_key}'.")
            return None

        logger.info(f"Successfully queried '{path}'. Result: {result}")
        return result
