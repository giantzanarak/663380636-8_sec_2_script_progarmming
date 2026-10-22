# agentic-spreadsheet-processor/main.py
import os

# Import through the 'src' package so the relative imports inside src/ work
from src.utils import setup_logging
from src.config_parser import ConfigParser
from src.spreadsheet_agent import SpreadsheetAgent

logger = setup_logging(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """
    Main entry point for the Agentic Spreadsheet Processor.
    Loads config and runs the agent.
    """
    config_file_path = os.path.join(BASE_DIR, 'configs', 'example_spreadsheet_config.json')

    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

        logger.info(f"Loading configuration from: {config_file_path}")
        config = ConfigParser(config_file_path).load_config()

        # Paths in the config are relative to the project root
        config["input_file"] = os.path.join(BASE_DIR, config["input_file"])
        config["output_file"] = os.path.join(BASE_DIR, config["output_file"])

        if not os.path.exists(config["input_file"]):
            logger.critical(f"Input Excel file not found: '{config['input_file']}'. Run 'python create_dummy_data.py' first.")
            return

        logger.info("Initializing Spreadsheet Agent...")
        agent = SpreadsheetAgent(config)

        logger.info("Running Spreadsheet Agent...")
        if agent.run():
            logger.info("Spreadsheet automation completed successfully.")
        else:
            logger.error("Spreadsheet automation finished with errors. Check the log above.")

    except FileNotFoundError as e:
        logger.critical(f"File system error: {e}")
        logger.info("Please ensure all specified input files and configurations exist.")
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        logger.info("Please check the format and required fields in your config file.")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred during execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
