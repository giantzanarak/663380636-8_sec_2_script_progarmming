# spreadsheet-automator/create_sample_data.py
# Creates data/input_sales.xlsx with sample sales data (Product Name, Quantity, Unit Price).
import os

import openpyxl
from openpyxl.styles import Font

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "input_sales.xlsx")

SALES = [
    ("Laptop", 2, 1200.50),
    ("Mouse", 5, 25.00),
    ("Keyboard", 3, 75.99),
    ("Monitor", 1, 300.00),
    ("Printer", 1, 150.00),
]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Sales"
ws.append(["Product Name", "Quantity", "Unit Price"])
for cell in ws[1]:
    cell.font = Font(bold=True)
for row in SALES:
    ws.append(row)
for letter, width in zip("ABC", (16, 10, 12)):
    ws.column_dimensions[letter].width = width

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
wb.save(OUTPUT_PATH)
print(f"Created {OUTPUT_PATH}")
