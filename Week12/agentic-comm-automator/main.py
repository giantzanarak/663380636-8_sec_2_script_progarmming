# agentic-comm-automator/main.py
import argparse
import datetime
import os
import sys

# Import through the 'src' package so the relative imports inside src/ work
from src.utils import setup_logging, ensure_directory_exists, get_env_variable, BASE_DIR
from src.config_parser import ConfigParser
from src.communication_agent import CommunicationAgent
from src.email_tasks import EmailTasks, MockEmailTasks

logger = setup_logging(__name__)

PLACEHOLDER_VALUES = {"", "your_gmail_address@gmail.com", "your_generated_gmail_app_password"}

def choose_mode(cli_mode):
    """--live/--mock beats COMM_MODE in .env; otherwise live only if real credentials are set."""
    if cli_mode:
        return cli_mode
    env_mode = os.getenv("COMM_MODE", "").strip().lower()
    if env_mode in ("live", "mock"):
        return env_mode
    has_credentials = (os.getenv("SENDER_EMAIL", "") not in PLACEHOLDER_VALUES and
                       os.getenv("SENDER_APP_PASSWORD", "") not in PLACEHOLDER_VALUES)
    return "live" if has_credentials else "mock"

def build_email_tasks(mode):
    if mode == "live":
        return EmailTasks(get_env_variable("SMTP_SERVER", "smtp.gmail.com"),
                          int(get_env_variable("SMTP_PORT", "587")),
                          get_env_variable("IMAP_SERVER", "imap.gmail.com"),
                          get_env_variable("SENDER_EMAIL"),
                          get_env_variable("SENDER_APP_PASSWORD"))

    # Mock mode: fill in demo addresses for anything not configured, so ${...} in the config resolves
    if os.getenv("SENDER_EMAIL", "") in PLACEHOLDER_VALUES:
        os.environ["SENDER_EMAIL"] = "agent@example.com"
    for name in ["TEST_RECIPIENT_EMAIL", "TEST_SMS_PHONE_NUMBER"]:
        if os.getenv(name, "") in PLACEHOLDER_VALUES:
            os.environ[name] = os.environ["SENDER_EMAIL"]
    os.environ.setdefault("TEST_SMS_CARRIER", "")
    logger.warning("Running in MOCK mode: no real email/SMS is sent. Messages are saved in data/outbox/.")
    return MockEmailTasks(os.environ["SENDER_EMAIL"], os.path.join(BASE_DIR, "data"))

def main():
    parser = argparse.ArgumentParser(description="Agentic Communication Automator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--live", dest="mode", action="store_const", const="live", help="send/receive through the real mail server")
    group.add_argument("--mock", dest="mode", action="store_const", const="mock", help="use the offline mock mailbox")
    args = parser.parse_args()

    config_file_path = os.path.join(BASE_DIR, 'configs', 'comm_pipeline_config.json')
    try:
        for folder in [os.path.join('data', 'reports'), os.path.join('data', 'incoming_attachments'), 'reports']:
            ensure_directory_exists(os.path.join(BASE_DIR, folder))

        mode = choose_mode(args.mode)
        email_tasks = build_email_tasks(mode)

        logger.info(f"Loading configuration from: {config_file_path}")
        config = ConfigParser(config_file_path).load_config()

        missing = [p for task in config['tasks'] for p in task.get('parameters', {}).get('attachments', [])
                   if not os.path.exists(os.path.join(BASE_DIR, p))]
        if missing:
            logger.critical(f"Attachment files not found: {missing}. Run 'python create_sample_files.py' first.")
            sys.exit(1)

        # Simulated "report" data the templates use (in a real system this comes from earlier pipelines)
        context = {
            "report_name": "DailySalesSummary",
            "report_date": datetime.date.today().strftime("%Y-%m-%d"),
            "sales_figure": 12345.67,
            "total_customers": 500,
            "self_email": os.environ["SENDER_EMAIL"],
        }

        agent = CommunicationAgent(config, BASE_DIR, email_tasks, context)
        logger.info("Running Communication Agent workflow...")
        if agent.run():
            logger.info("Communication automation process completed successfully.")
        else:
            logger.error("Communication automation finished with errors. See the audit report in reports/.")
            sys.exit(1)

    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
