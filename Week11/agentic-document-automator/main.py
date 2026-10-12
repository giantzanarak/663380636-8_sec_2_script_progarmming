# agentic-document-automator/main.py
import os

# Import through the 'src' package so the relative imports inside src/ work
from src.config_parser import ConfigParser
from src.document_agent import DocumentAgent
from src.utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Task fields that hold paths relative to the project root
PATH_FIELDS = ['template_path', 'output_path', 'input_pdf', 'output_pdf', 'input_docx', 'output_text_file']
# Fields that must already exist before the run (outputs of earlier tasks are excluded)
INPUT_FIELDS = ['template_path', 'input_pdf', 'input_pdfs']

def resolve_paths(config):
    """Turns every relative path in the config into an absolute path under BASE_DIR."""
    for key, value in config.get('output_files', {}).items():
        config['output_files'][key] = os.path.join(BASE_DIR, value)
    for task in config['tasks']:
        for field in PATH_FIELDS:
            if field in task:
                task[field] = os.path.join(BASE_DIR, task[field])
        if 'input_pdfs' in task:
            task['input_pdfs'] = [os.path.join(BASE_DIR, p) for p in task['input_pdfs']]

def check_required_files(config):
    """Checks that template / input PDFs exist before the agent starts."""
    produced = set()
    missing = []
    for task in config['tasks']:
        for field in INPUT_FIELDS:
            paths = task.get(field, [])
            for path in paths if isinstance(paths, list) else [paths]:
                if path not in produced and not os.path.exists(path):
                    missing.append(path)
        produced.update(task[f] for f in ['output_path', 'output_pdf'] if f in task)
    for path in missing:
        logger.critical(f"Required input file not found: {path}")
    return not missing

def main():
    config_file_path = os.path.join(BASE_DIR, 'configs', 'document_automation_config.json')

    try:
        ensure_directory_exists(os.path.join(BASE_DIR, 'documents'))
        ensure_directory_exists(os.path.join(BASE_DIR, 'templates'))

        config = ConfigParser(config_file_path).load_config()
        resolve_paths(config)

        if not check_required_files(config):
            logger.critical("Missing required input files! Run 'python create_sample_files.py' first.")
            return

        agent = DocumentAgent(config, reports_dir=os.path.join(BASE_DIR, 'documents', 'reports'))
        if agent.run():
            logger.info("Document automation process completed successfully.")
        else:
            logger.error("Document automation finished with errors. See the audit report for details.")

    except FileNotFoundError as e:
        logger.critical(f"File system error: {e}")
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
