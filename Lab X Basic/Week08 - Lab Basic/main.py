# data-processor/main.py
import os
import sys

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from csv_handler import CSVHandler
from json_handler import JSONHandler
from utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

DEFAULT_SALES_FIELDS = ['OrderID', 'Product', 'Amount', 'Price', 'Customer']

def main():
    """
    Main entry point for the CSV and JSON data processor.
    """
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    ensure_directory_exists(data_dir)

    # --- File Paths ---
    input_csv_path = os.path.join(data_dir, 'input_sales.csv')
    output_filtered_csv_path = os.path.join(data_dir, 'output_filtered_sales.csv')
    input_json_path = os.path.join(data_dir, 'input_inventory.json')
    output_updated_json_path = os.path.join(data_dir, 'output_updated_inventory.json')

    # --- Initialize Handlers ---
    csv_proc = CSVHandler()
    json_proc = JSONHandler()

    logger.info("--- Starting CSV Data Processing Workflow ---")

    # 1. Read CSV data
    sales_data = csv_proc.read_csv_as_dicts(input_csv_path)

    if sales_data:
        # 2. Process sales data (filter sales >= $100 and get summary)
        min_amount_for_filter = 100.0
        processed_results = csv_proc.process_sales_data(sales_data, min_sale_amount=min_amount_for_filter)
        filtered_sales = processed_results["filtered_sales"]
        sales_summary = processed_results["summary"]

        logger.info(f"Summary of all sales: {sales_summary}")

        # 3. Prepare data for writing, including a summary row
        csv_fieldnames = list(sales_data[0].keys()) or DEFAULT_SALES_FIELDS

        summary_row = {
            'OrderID': 'SUMMARY',
            'Product': 'Total/Avg',
            'Amount': sales_summary['Total Sales'],
            'Price': sales_summary['Average Item Price'],
            'Customer': f"Count: {sales_summary['Filtered Sales Count']}"
        }
        filtered_sales_with_summary = filtered_sales + [summary_row]

        # 4. Write filtered sales data to a new CSV
        csv_proc.write_dicts_to_csv(filtered_sales_with_summary, output_filtered_csv_path, csv_fieldnames)
    else:
        logger.error("No sales data to process from CSV.")

    logger.info("--- Starting JSON Data Processing Workflow ---")

    # 1. Read JSON inventory data
    inventory_data = json_proc.read_json(input_json_path)

    if inventory_data:
        # 2. Update existing product stock
        json_proc.update_inventory(inventory_data, "PROD001", 60) # Update Laptop Pro stock
        json_proc.update_inventory(inventory_data, "PROD003", 75) # Update Ergonomic Mouse stock

        # 3. Add a new product
        new_product_entry = {
            "id": "PROD004",
            "name": "Gaming Headset",
            "category": "Audio",
            "stock": 90,
            "details": {
                "brand": "SoundBlaster",
                "features": ["Noise Cancelling", "RGB"]
            }
        }
        json_proc.add_product(inventory_data, new_product_entry)

        # 4. Write updated JSON data to a new file (the input file is left unchanged)
        json_proc.write_json(inventory_data, output_updated_json_path, indent=2)
    else:
        logger.error("No inventory data to process from JSON.")

    logger.info("--- Data Processing Workflows Completed ---")

if __name__ == "__main__":
    main()
