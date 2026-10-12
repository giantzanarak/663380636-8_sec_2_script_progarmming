# agentic-document-automator/src/pdf_tasks.py
import io
import os

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class PDFTasks:
    """Handles PDF operations (watermark, merge, text extraction) for the Document Agent."""
    def __init__(self):
        logger.info("PDFTasks initialized.")

    def _create_text_watermark_page(self, watermark_text, page_width, page_height,
                                    font_size=50, color=(0, 0, 0, 0.2), angle=45):
        """Draws the watermark text with reportlab (in memory) and returns it as a pypdf page."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        r, g, b, a = color
        c.setFillColor(Color(r, g, b, alpha=a))
        c.setFont('Helvetica-Bold', font_size)
        c.translate(page_width / 2, page_height / 2)
        c.rotate(angle)
        text_width = c.stringWidth(watermark_text, 'Helvetica-Bold', font_size)
        c.drawString(-text_width / 2, -font_size / 4, watermark_text)
        c.showPage()
        c.save()
        buffer.seek(0)
        return PdfReader(buffer).pages[0]

    def apply_watermark(self, input_pdf_path, output_pdf_path, watermark_text,
                        font_size=50, color=(0.5, 0.5, 0.5, 0.2), angle=45):
        """Stamps `watermark_text` diagonally on every page of a PDF."""
        if not os.path.exists(input_pdf_path):
            logger.error(f"Input PDF for watermarking not found: {input_pdf_path}")
            return False

        ensure_directory_exists(os.path.dirname(output_pdf_path))
        try:
            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()
            for page in reader.pages:
                # Build the watermark at this page's size so it is centred on any page format
                width, height = float(page.mediabox.width), float(page.mediabox.height)
                page.merge_page(self._create_text_watermark_page(watermark_text, width, height, font_size, color, angle))
                writer.add_page(page)
            with open(output_pdf_path, 'wb') as f:
                writer.write(f)
            logger.info(f"Watermark '{watermark_text}' applied to {len(reader.pages)} page(s). Output: '{output_pdf_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error applying watermark to '{input_pdf_path}': {e}")
            return False

    def merge_pdfs(self, pdf_paths, output_path):
        """Merges several PDFs (in the given order) into one file."""
        if not pdf_paths:
            logger.error("No PDF files given to merge.")
            return False

        writer = PdfWriter()
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                logger.warning(f"PDF to merge not found, skipping: {pdf_path}")
                continue
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Added {len(reader.pages)} page(s) from '{pdf_path}'.")
            except Exception as e:
                logger.error(f"Error reading PDF '{pdf_path}': {e}")

        if len(writer.pages) == 0:
            logger.error("Nothing to merge: no pages were read.")
            return False
        try:
            ensure_directory_exists(os.path.dirname(output_path))
            with open(output_path, 'wb') as f:
                writer.write(f)
            logger.info(f"Merged {len(writer.pages)} page(s) into '{output_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error writing merged PDF: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path):
        """Returns the text of every page, separated by page markers."""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF not found: {pdf_path}")
            return None
        try:
            reader = PdfReader(pdf_path)
            pages_text = [f"--- Page {i} ---\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages, start=1)]
            logger.info(f"Text extracted from {len(reader.pages)} page(s) of '{pdf_path}'.")
            return "\n\n".join(pages_text)
        except Exception as e:
            logger.error(f"Error extracting text from '{pdf_path}': {e}")
            return None
