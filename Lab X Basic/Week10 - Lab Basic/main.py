# spreadsheet-automator/main.py
import os
import sys

# Add the 'src' directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from excel_processor import ExcelProcessor


def main():
    """
    Main entry point for the spreadsheet automation application.
    Paths are based on this file's folder, so it works from any working directory.
    """
    data_dir = os.path.join(BASE_DIR, "data")
    input_file = os.path.join(data_dir, "input_sales.xlsx")
    output_file = os.path.join(data_dir, "output_sales_report.xlsx")
    os.makedirs(data_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        print("Run 'python create_sample_data.py' to create it, or add your own file with the columns "
              "Product Name, Quantity, Unit Price.")
        return

    processor = ExcelProcessor()
    print(f"Starting sales data processing from '{input_file}'...")
    if processor.process_sales_data(input_file, output_file):
        print(f"Sales report successfully generated and saved to '{output_file}'.")
    else:
        print("Failed to generate sales report.")


if __name__ == "__main__":
    main()
