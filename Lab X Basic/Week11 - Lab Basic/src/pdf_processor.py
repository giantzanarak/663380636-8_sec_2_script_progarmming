# document-automator/src/pdf_processor.py
import os

from pypdf import PdfReader, PdfWriter  # pypdf is the maintained successor of PyPDF2 (same API)

from utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class PDFProcessor:
    """
    Handles operations on PDF files: text extraction, merging and splitting.
    """
    def __init__(self):
        logger.info("PDFProcessor initialized.")

    def extract_pages_text(self, pdf_path):
        """
        Extracts the text of each page. Returns a list of strings (one per page),
        or None if the file is missing or cannot be read.
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        try:
            reader = PdfReader(pdf_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            logger.info(f"Extracted text from '{os.path.basename(pdf_path)}' ({len(pages)} pages).")
            return pages
        except Exception as e:
            logger.error(f"Error extracting text from '{pdf_path}': {e}")
            return None

    def extract_text_from_pdf(self, pdf_path):
        """Extracts all text as one string, with a '--- Page End ---' marker after each page."""
        pages = self.extract_pages_text(pdf_path)
        if pages is None:
            return None
        return "".join(text + "\n--- Page End ---\n" for text in pages)

    def merge_pdfs(self, pdf_paths, output_path):
        """
        Merges multiple PDF files (in the given order) into a single output PDF.
        Returns the number of pages written (0 if nothing was merged).
        """
        if not pdf_paths:
            logger.warning("No PDF paths provided for merging.")
            return 0

        writer = PdfWriter()
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                logger.warning(f"Skipping non-existent PDF for merging: {pdf_path}")
                continue
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Added '{os.path.basename(pdf_path)}' ({len(reader.pages)} page(s)) to the merge.")
            except Exception as e:
                logger.error(f"Error reading PDF '{pdf_path}' for merging: {e}")

        if len(writer.pages) == 0:
            logger.warning("No pages were added - merged PDF not created.")
            return 0

        try:
            ensure_directory_exists(os.path.dirname(output_path))
            with open(output_path, 'wb') as f:
                writer.write(f)
            logger.info(f"PDFs successfully merged to '{os.path.basename(output_path)}' ({len(writer.pages)} pages).")
            return len(writer.pages)
        except Exception as e:
            logger.error(f"Error writing merged PDF to '{output_path}': {e}")
            return 0

    def split_pdf(self, pdf_path, output_dir=".", pages_per_split=1):
        """
        Splits a PDF into smaller PDFs of `pages_per_split` pages each.
        Returns the list of files created.
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        ensure_directory_exists(output_dir)

        created = []
        try:
            reader = PdfReader(pdf_path)
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            for start in range(0, len(reader.pages), pages_per_split):
                writer = PdfWriter()
                for page in reader.pages[start:start + pages_per_split]:
                    writer.add_page(page)
                output_file = os.path.join(output_dir, f"{base_name}_part_{start // pages_per_split + 1}.pdf")
                with open(output_file, 'wb') as f:
                    writer.write(f)
                created.append(output_file)
            logger.info(f"Split '{os.path.basename(pdf_path)}' into {len(created)} file(s).")
        except Exception as e:
            logger.error(f"Error splitting PDF '{pdf_path}': {e}")
        return created
