"""
email-sms-automator/main.py
Runs the communication workflow:
  1. send a plain-text email
  2. send an email with an attachment
  3. send an SMS via an email-to-SMS gateway
  4. send an email to yourself, then find it in the inbox, read it and download its attachment

Usage:
    python main.py            # real run (needs .env with a Gmail App Password)
    python main.py --dry-run  # test the workflow without sending or reading any email
"""

import argparse
import os
import sys
import time

# Make the 'src' modules importable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from email_receiver import EmailReceiver
from email_sender import EmailSender
from sms_gateway import SMSGateway
from utils import ensure_directory_exists, get_env_variable, setup_logging

logger = setup_logging(__name__)

RECEIVE_DEMO_SUBJECT = "Python Test: Email for Receiving Demo"


def load_settings():
    """Reads all settings from .env. Exits with a clear message if something required is missing."""
    try:
        return {
            "sender_email": get_env_variable("SENDER_EMAIL"),
            "app_password": get_env_variable("SENDER_APP_PASSWORD"),
            "smtp_server": get_env_variable("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(get_env_variable("SMTP_PORT", "587")),
            "imap_server": get_env_variable("IMAP_SERVER", "imap.gmail.com"),
            "recipient": get_env_variable("TEST_RECIPIENT_EMAIL"),
            "sms_number": get_env_variable("TEST_SMS_PHONE_NUMBER", ""),
            "sms_carrier": get_env_variable("TEST_SMS_CARRIER", ""),
            "student_info": get_env_variable("STUDENT_INFO"),
        }
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        logger.info("Copy .env.example to .env and fill in your values.")
        sys.exit(1)


def receive_demo(settings, attachments_dir, attempts=4, delay=5):
    """Task 4b: find the demo email in the inbox (retrying while it is delivered) and process it."""
    with EmailReceiver(settings["imap_server"], settings["sender_email"], settings["app_password"]) as receiver:
        if not receiver.mail:
            return
        uids = []
        for attempt in range(1, attempts + 1):
            uids = receiver.search_emails(criteria='UNSEEN', from_sender=settings["sender_email"],
                                          subject_contains=RECEIVE_DEMO_SUBJECT)
            if uids or attempt == attempts:
                break
            logger.info(f"Demo email not in the inbox yet (attempt {attempt}/{attempts}), waiting {delay}s...")
            time.sleep(delay)

        if not uids:
            logger.info("No matching unread emails found for the receiving demo.")
            return
        for uid in uids:
            details = receiver.fetch_email_content(uid, mark_as_read=True, download_attachments_dir=attachments_dir)
            if not details:
                continue
            logger.info(f"  Sender:  {details['sender']}")
            logger.info(f"  Subject: {details['subject']}")
            logger.info(f"  Body:    {details['body_snippet']}")
            files = [os.path.basename(p) for p in details['attachments_downloaded']]
            logger.info(f"  Attachments downloaded: {', '.join(files) if files else 'none'}")


def main():
    parser = argparse.ArgumentParser(description="Email & SMS automator")
    parser.add_argument("--dry-run", action="store_true", help="log what would be sent; send/read nothing")
    args = parser.parse_args()

    data_dir = os.path.join(BASE_DIR, 'data')
    attachments_dir = os.path.join(data_dir, 'attachments')
    ensure_directory_exists(attachments_dir)
    attachment_file_path = os.path.join(data_dir, 'dummy_report.pdf')
    attachment = attachment_file_path if os.path.exists(attachment_file_path) else None
    if attachment is None:
        logger.warning("data/dummy_report.pdf not found - run 'python create_sample_files.py'. "
                       "Emails will be sent without the attachment.")

    s = load_settings()
    info = s["student_info"]
    sender = EmailSender(s["smtp_server"], s["smtp_port"], s["sender_email"], s["app_password"], dry_run=args.dry_run)
    sms = SMSGateway(sender)
    results = {}

    logger.info("--- Task 1: Sending a simple plaintext email ---")
    results["Task 1 plain email"] = sender.send_email(
        recipient_email=s["recipient"],
        subject="ทดสอบ Automated Python Test Email",
        body=f"{info}\n\nThis is an automated test email sent with Python (smtplib).")

    logger.info("--- Task 2: Sending an email with an attachment ---")
    results["Task 2 email + attachment"] = sender.send_email(
        recipient_email=s["recipient"],
        subject="ทดสอบ Python Test Email with Attachment - Daily Report",
        body=f"{info}\n\nPlease find the daily report attached.",
        attachment_path=attachment)

    logger.info("--- Task 3: Sending an SMS via email gateway ---")
    results["Task 3 SMS"] = sms.send_sms(
        phone_number=s["sms_number"],
        message=f"ทดสอบ SMS from Python - {info}",
        carrier_name=s["sms_carrier"])

    logger.info("--- Task 4: Receiving and processing emails ---")
    results["Task 4 demo email to self"] = sender.send_email(
        recipient_email=s["sender_email"],
        subject=f"ทดสอบ {RECEIVE_DEMO_SUBJECT}",
        body=f"{info}\n\nThis email is for the receiving demo. It has an attachment.",
        attachment_path=attachment)
    if args.dry_run:
        logger.info("[DRY RUN] Skipping inbox search.")
    elif results["Task 4 demo email to self"]:
        receive_demo(s, attachments_dir)

    logger.info("--- Summary ---")
    for task, ok in results.items():
        logger.info(f"  {'OK  ' if ok else 'FAIL'}  {task}")
    logger.info("--- All communication automation tasks completed ---")


if __name__ == "__main__":
    main()
