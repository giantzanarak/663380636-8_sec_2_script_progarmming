# agentic-data-processor/src/csv_tasks.py
import csv
import os
from collections import defaultdict
from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class CSVTasks:
    """
    Handles advanced reading, writing, and processing of CSV files.
    All data is handled as a list of dictionaries.
    """
    def __init__(self):
        logger.info("CSVTasks initialized.")

    def load_csv(self, file_path):
        """
        Loads a CSV file and returns its content as a list of dictionaries.
        Assumes the first row is the header.
        """
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
            logger.info(f"Successfully loaded {len(data)} rows from '{file_path}'.")
            return data
        except Exception as e:
            logger.error(f"Error loading CSV file '{file_path}': {e}")
            return None

    def save_csv(self, data, file_path, fieldnames=None):
        """
        Saves a list of dictionaries to a CSV file.
        `fieldnames` can be explicitly provided or inferred from the first dictionary.
        """
        if not data:
            logger.warning("No data provided to save to CSV. File will be empty or not created.")
            return False

        ensure_directory_exists(os.path.dirname(file_path))

        if fieldnames is None:
            # Infer fieldnames from the first dictionary
            if isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
                logger.info(f"Inferred fieldnames for CSV: {fieldnames}")
            else:
                logger.error("Cannot infer fieldnames: data is not a list of dictionaries.")
                return False

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Successfully saved {len(data)} rows to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving CSV file '{file_path}': {e}")
            return False

    def transform_csv_aggregate(self, data, group_by_field, aggregate_field, aggregate_type="sum"):
        """
        Aggregates CSV data (list of dicts) by a specified field.
        Supports 'sum', 'count', 'average'.
        Assumes aggregate_field can be converted to float for sum/average.
        """
        if not data:
            logger.warning("No data to aggregate.")
            return []

        aggregated_data = defaultdict(lambda: {'_count': 0, '_sum': 0.0})

        for row in data:
            group_value = row.get(group_by_field)
            if group_value is None:
                logger.warning(f"Skipping row due to missing group_by_field '{group_by_field}': {row}")
                continue

            try:
                numeric_value = float(row.get(aggregate_field, 0)) # Default to 0 if field missing
                aggregated_data[group_value]['_sum'] += numeric_value
                aggregated_data[group_value]['_count'] += 1
            except ValueError as e:
                logger.warning(f"Skipping aggregation for row due to non-numeric '{aggregate_field}': {row}. Error: {e}")
                continue
            except TypeError as e:
                logger.warning(f"Skipping aggregation for row due to missing aggregate_field '{aggregate_field}': {row}. Error: {e}")
                continue

        results = []
        for group_value, metrics in aggregated_data.items():
            result_row = {group_by_field: group_value}
            if aggregate_type == "sum":
                result_row[f'Total_{aggregate_field}'] = round(metrics['_sum'], 2)
            elif aggregate_type == "count":
                result_row[f'Count_{aggregate_field}'] = metrics['_count']
            elif aggregate_type == "average":
                result_row[f'Average_{aggregate_field}'] = round(metrics['_sum'] / metrics['_count'], 2) if metrics['_count'] > 0 else 0.0
            else:
                logger.warning(f"Unsupported aggregation type: {aggregate_type}. Skipping for group {group_value}.")
                continue
            results.append(result_row)

        logger.info(f"Aggregated data by '{group_by_field}' using '{aggregate_type}'. Produced {len(results)} rows.")
        return results

    def filter_csv(self, data, filter_field, operator, value):
        """
        Filters CSV data (list of dicts) based on a condition.
        `operator` can be '>', '<', '>=', '<=', '==', '!='.
        `value` will be converted to appropriate type if possible.
        """
        if not data:
            logger.warning("No data to filter.")
            return []

        operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
        }
        if operator not in operators:
            logger.warning(f"Unsupported filter operator: '{operator}'. No rows filtered.")
            return []

        filtered_data = []
        for row in data:
            field_value = row.get(filter_field)
            if field_value is None:
                logger.debug(f"Skipping row in filter due to missing field '{filter_field}': {row}")
                continue
            try:
                # Attempt type conversion for comparison
                if isinstance(value, (int, float)):
                    compare_value = float(field_value)
                else: # Default to string comparison
                    compare_value = str(field_value)

                if operators[operator](compare_value, value):
                    filtered_data.append(row)
            except ValueError as e:
                logger.warning(f"Type conversion error during filter for row: {row}. Error: {e}")

        logger.info(f"Filtered data by '{filter_field} {operator} {value}'. Resulted in {len(filtered_data)} rows.")
        return filtered_data
