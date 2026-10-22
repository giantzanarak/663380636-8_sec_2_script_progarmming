# data-processor/src/csv_handler.py
import csv
import os
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)

class CSVHandler:
    """
    Handles reading, writing, and basic processing of CSV files.
    """
    def __init__(self):
        logger.info("CSVHandler initialized.")

    def read_csv_as_dicts(self, file_path):
        """
        Reads a CSV file and returns its content as a list of dictionaries.
        Assumes the first row is the header.
        """
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return None

        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
            logger.info(f"Successfully read {len(data)} rows from '{file_path}'.")
            return data
        except Exception as e:
            logger.error(f"Error reading CSV file '{file_path}': {e}")
            return None

    def write_dicts_to_csv(self, data, file_path, fieldnames):
        """
        Writes a list of dictionaries to a CSV file.
        `fieldnames` must be a list of strings corresponding to dictionary keys for headers.
        """
        if not data:
            logger.warning("No data provided to write to CSV.")
            return False

        ensure_directory_exists(os.path.dirname(file_path))

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Successfully wrote {len(data)} rows to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing CSV file '{file_path}': {e}")
            return False

    def process_sales_data(self, sales_data, min_sale_amount=0):
        """
        Processes sales data: calculates total sales, average price,
        and filters sales above a certain amount.
        Assumes 'Amount' and 'Price' fields are present and convertible to float.
        """
        if not sales_data:
            logger.warning("No sales data provided for processing.")
            return {"filtered_sales": [], "summary": {}}

        total_sales = 0.0
        total_price = 0.0
        num_items = 0
        filtered_sales = []

        for row in sales_data:
            try:
                amount = float(row.get('Amount') or 0)
                price = float(row.get('Price') or 0) # Assuming 'Price' per item
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to data conversion error: {row}. Error: {e}")
                continue

            total_sales += amount
            num_items += 1 # Count items for average price
            total_price += price

            if amount >= min_sale_amount:
                filtered_sales.append(row)

        average_price = total_price / num_items if num_items > 0 else 0.0

        summary = {
            "Total Sales": f"{total_sales:.2f}",
            "Average Item Price": f"{average_price:.2f}",
            "Filtered Sales Count": len(filtered_sales)
        }

        logger.info(f"Sales data processed. Total Sales: {summary['Total Sales']}, "
                    f"Filtered Count: {summary['Filtered Sales Count']}")
        return {"filtered_sales": filtered_sales, "summary": summary}
