# document-automator/main.py
import datetime
import os
import re
import sys

# Add the 'src' directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from pdf_processor import PDFProcessor
from word_processor import WordProcessor
from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)

NUMBERED_ITEM = re.compile(r"^\d+\.\s+")


def text_blocks(page_text):
    """Splits a page's text into blocks separated by blank lines; each block is a list of lines."""
    blocks, current = [], []
    for line in page_text.splitlines():
        line = line.strip()
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def add_page_content(word_proc, doc, page_text):
    """
    Writes one PDF page into the document, keeping its structure:
    a short line without a full stop becomes a heading, numbered lines become a numbered
    list, and other blocks become normal paragraphs.
    """
    for block in text_blocks(page_text):
        if len(block) == 1 and len(block[0]) < 60 and not block[0].endswith("."):
            word_proc.add_heading(doc, block[0], level=2)
        elif all(NUMBERED_ITEM.match(line) for line in block):
            for line in block:
                word_proc.add_paragraph(doc, NUMBERED_ITEM.sub("", line), style="List Number")
        else:
            word_proc.add_paragraph(doc, " ".join(block), align="justify")


def build_report(pdf_proc, word_proc, input_pdf_path, output_docx_path, merged_pages):
    """Task 1: extract text from the PDF and create the Word report. Returns True on success."""
    pages = pdf_proc.extract_pages_text(input_pdf_path)
    if not pages or not any(page.strip() for page in pages):
        logger.error("Could not extract text from PDF. Skipping Word document generation.")
        return False

    doc = word_proc.create_document()
    word_proc.add_heading(doc, "Automated Document Report", level=0)
    word_proc.add_paragraph(doc, "This report was automatically generated from PDF content and structured data.",
                            bold=True, font_size=12)
    word_proc.add_paragraph(doc, f"--- Extracted Content from {os.path.basename(input_pdf_path)} ---",
                            italic=True, font_size=10, align="center")

    for page_number, page_text in enumerate(pages, start=1):
        add_page_content(word_proc, doc, page_text)
        word_proc.add_paragraph(doc, f"--- Page {page_number} End ---", italic=True, font_size=9, align="center")

    all_text = "\n".join(pages)
    word_proc.add_heading(doc, "Summary Data", level=1)
    table_data = [
        ["Metric", "Value", "Notes"],
        ["Source File", os.path.basename(input_pdf_path), "Input PDF"],
        ["Total Pages Processed", str(len(pages)), "From Input PDF"],
        ["Words Extracted", str(len(all_text.split())), "All pages"],
        ["Merged PDF Pages", str(merged_pages), "dummy_doc1.pdf + dummy_doc2.pdf"],
        ["Document Type", "PDF/Word Hybrid", ""],
        ["Generated Date", datetime.date.today().isoformat(), ""],
    ]
    word_proc.add_table(doc, table_data, col_widths=[1.8, 2.0, 2.6])

    return word_proc.save_document(doc, output_docx_path)


def main():
    """
    Main entry point for the document automation application.
    """
    documents_dir = os.path.join(BASE_DIR, 'documents')
    ensure_directory_exists(documents_dir)

    input_pdf_path = os.path.join(documents_dir, 'input_article.pdf')
    output_docx_path = os.path.join(documents_dir, 'output_report.docx')
    merged_pdf_output_path = os.path.join(documents_dir, 'merged_output.pdf')
    pdfs_to_merge = [os.path.join(documents_dir, 'dummy_doc1.pdf'), os.path.join(documents_dir, 'dummy_doc2.pdf')]

    if not os.path.exists(input_pdf_path):
        logger.critical(f"Required input PDF '{input_pdf_path}' not found.")
        logger.info("Put input_article.pdf (from the course Google Drive folder) into the 'documents' folder.")
        return

    pdf_proc = PDFProcessor()
    word_proc = WordProcessor()
    logger.info("--- Starting Document Automation Workflow ---")

    # Task 2 runs first so the report can include the number of merged pages
    logger.info("Task 2: Merging dummy PDFs.")
    missing = [os.path.basename(p) for p in pdfs_to_merge if not os.path.exists(p)]
    if missing:
        logger.warning(f"Skipping PDF merge: missing {', '.join(missing)}.")
        merged_pages = 0
    else:
        merged_pages = pdf_proc.merge_pdfs(pdfs_to_merge, merged_pdf_output_path)

    logger.info("Task 1: Extracting text from PDF and generating Word report.")
    build_report(pdf_proc, word_proc, input_pdf_path, output_docx_path, merged_pages)

    logger.info("--- Document Automation Workflow Completed ---")


if __name__ == "__main__":
    main()
