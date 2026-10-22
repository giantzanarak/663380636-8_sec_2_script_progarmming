# data-processor/src/json_handler.py
import json
import os
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)

class JSONHandler:
    """
    Handles reading, writing, and basic manipulation of JSON files.
    """
    def __init__(self):
        logger.info("JSONHandler initialized.")

    def read_json(self, file_path):
        """Reads a JSON file and returns the Python object."""
        if not os.path.exists(file_path):
            logger.error(f"JSON file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Successfully read JSON from '{file_path}'.")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading JSON file '{file_path}': {e}")
            return None

    def write_json(self, data, file_path, indent=4):
        """Writes a Python object to a JSON file, with pretty-printing."""
        ensure_directory_exists(os.path.dirname(file_path))

        try:
            with open(file_path, mode='w', encoding='utf-8') as file:
                json.dump(data, file, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully wrote JSON to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file '{file_path}': {e}")
            return False

    def update_inventory(self, inventory_data, product_id, new_stock_level):
        """
        Updates the stock level of a product in nested inventory data.
        Assumes inventory_data is a list of product dictionaries.
        """
        if not isinstance(inventory_data, list):
            logger.warning("Inventory data is not a list. Cannot update.")
            return False

        for product in inventory_data:
            if product.get("id") == product_id:
                old_stock = product.get("stock")
                product["stock"] = new_stock_level
                logger.info(f"Updated stock for product '{product_id}' from {old_stock} to {new_stock_level}.")
                return True

        logger.warning(f"Product '{product_id}' not found in inventory for update.")
        return False

    def add_product(self, inventory_data, new_product):
        """Adds a new product dictionary to the inventory list (skips duplicate IDs)."""
        if not isinstance(inventory_data, list):
            logger.warning("Inventory data is not a list. Cannot add product.")
            return False

        if any(product.get("id") == new_product.get("id") for product in inventory_data):
            logger.warning(f"Product '{new_product.get('id')}' already exists. Not added again.")
            return False

        inventory_data.append(new_product)
        logger.info(f"Added new product: {new_product.get('name', 'N/A')}.")
        return True
