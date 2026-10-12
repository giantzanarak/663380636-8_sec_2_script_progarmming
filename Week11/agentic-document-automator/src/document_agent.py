# agentic-document-automator/src/document_agent.py
import os
import json
import datetime

from .utils import setup_logging, log_audit_entry, ensure_directory_exists
from .pdf_tasks import PDFTasks
from .word_tasks import WordTasks

logger = setup_logging(__name__)

class DocumentAgent:
    """
    Runs the document tasks listed in the configuration (Word reports, PDF watermark/merge,
    text extraction) and writes an audit report of every step.
    """
    def __init__(self, config, reports_dir="documents/reports"):
        self.config = config
        self.reports_dir = reports_dir
        self.audit_log = []
        self.start_time = datetime.datetime.now()
        self.pdf_processor = PDFTasks()
        self.word_processor = WordTasks()

        # Task dispatcher: maps the task 'type' in the config to its handler method
        self.task_handlers = {
            "generate_word_report": self._handle_generate_word_report,
            "apply_pdf_watermark": self._handle_apply_pdf_watermark,
            "merge_pdfs": self._handle_merge_pdfs,
            "extract_word_text": self._handle_extract_word_text,
            "extract_pdf_text": self._handle_extract_pdf_text,
        }
        logger.info("Document Agent initialized.")

    # --- Task handlers (each returns True on success) ---------------------------

    def _handle_generate_word_report(self, task):
        # Task-specific data overrides the global data (e.g. REPORT_DATE, AUTHOR_NAME)
        placeholders = {**self.config.get("global_data", {}), **task.get("data", {})}
        return self.word_processor.generate_report_from_template(
            task["template_path"], task["output_path"], placeholders, task.get("table_data"))

    def _handle_apply_pdf_watermark(self, task):
        return self.pdf_processor.apply_watermark(
            task["input_pdf"], task["output_pdf"], task["watermark_text"],
            task.get("font_size", 50), tuple(task.get("color", [0.5, 0.5, 0.5, 0.2])), task.get("angle", 45))

    def _handle_merge_pdfs(self, task):
        return self.pdf_processor.merge_pdfs(task["input_pdfs"], task["output_pdf"])

    def _handle_extract_word_text(self, task):
        return self._save_text(self.word_processor.extract_text_from_word(task["input_docx"]), task["output_text_file"])

    def _handle_extract_pdf_text(self, task):
        return self._save_text(self.pdf_processor.extract_text_from_pdf(task["input_pdf"]), task["output_text_file"])

    @staticmethod
    def _save_text(text, output_path):
        if not text:
            return False
        ensure_directory_exists(os.path.dirname(output_path))
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"Text saved to '{output_path}'.")
        return True

    # -----------------------------------------------------------------------------

    def _process_task(self, task):
        task_type = task.get("type")
        task_name = task.get("name", task_type)
        log_audit_entry(self.audit_log, "INFO", f"Starting task '{task_name}'", task_type, task)

        handler = self.task_handlers.get(task_type)
        if handler is None:
            log_audit_entry(self.audit_log, "WARNING", f"Unsupported task type: {task_type}", task_type, task)
            return False
        try:
            success = handler(task)
        except Exception as e:
            log_audit_entry(self.audit_log, "ERROR", f"Error in '{task_name}': {e}", task_type, {"error": str(e)})
            return False

        if success:
            log_audit_entry(self.audit_log, "SUCCESS", f"Task '{task_name}' completed.", task_type)
        else:
            log_audit_entry(self.audit_log, "ERROR", f"Task '{task_name}' failed.", task_type)
        return success

    def _generate_audit_report(self):
        ensure_directory_exists(self.reports_dir)
        report_path = os.path.join(self.reports_dir, f"audit_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.audit_log, f, indent=4, ensure_ascii=False)
            logger.info(f"Audit report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}")

    def run(self):
        log_audit_entry(self.audit_log, "INFO", "Document Agent started.", "agent_run")
        tasks = self.config.get("tasks", [])
        succeeded = sum(1 for task in tasks if self._process_task(task))
        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        log_audit_entry(self.audit_log, "INFO", f"Finished {succeeded}/{len(tasks)} tasks successfully in {duration:.2f}s.",
                        "agent_run_summary")
        self._generate_audit_report()
        return succeeded == len(tasks)
