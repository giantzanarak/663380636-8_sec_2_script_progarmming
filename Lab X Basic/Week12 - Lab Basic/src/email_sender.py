"""
email-sms-automator/src/email_sender.py
Sends emails over SMTP with STARTTLS, optional HTML body and file attachments.
"""

import mimetypes
import os
import smtplib
from email.message import EmailMessage

try:
    from .utils import setup_logging
except ImportError:
    from utils import setup_logging

logger = setup_logging(__name__)


class EmailSender:
    """Sends emails via SMTP. With dry_run=True nothing is sent; the message is only logged."""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str,
                 dry_run: bool = False):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.dry_run = dry_run
        logger.info(f"EmailSender initialized for {sender_email} via {smtp_server}:{smtp_port}"
                    f"{' (DRY RUN - nothing will be sent)' if dry_run else ''}.")

    def build_message(self, recipient_email: str, subject: str, body: str,
                      attachment_path: str = None, is_html: bool = False) -> EmailMessage:
        """Builds the email (UTF-8, so Thai text in subject and body is encoded correctly)."""
        msg = EmailMessage()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.set_content(body, subtype='html' if is_html else 'plain')

        if attachment_path:
            if os.path.exists(attachment_path):
                content_type, _ = mimetypes.guess_type(attachment_path)
                maintype, subtype = (content_type or 'application/octet-stream').split('/', 1)
                with open(attachment_path, 'rb') as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                                       filename=os.path.basename(attachment_path))
                logger.info(f"Attached file: {os.path.basename(attachment_path)}")
            else:
                logger.error(f"Attachment file not found: {attachment_path}. Email will be sent without it.")
        return msg

    def send_email(self, recipient_email: str, subject: str, body: str,
                   attachment_path: str = None, is_html: bool = False) -> bool:
        """Sends one email. Returns True on success, False on any error (logged)."""
        msg = self.build_message(recipient_email, subject, body, attachment_path, is_html)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would send to {recipient_email} | Subject: '{subject}' | Body: '{body[:80]}'")
            return True

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()  # encrypt the connection before logging in
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email} with subject: '{subject}'.")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed - check SENDER_EMAIL and the App Password. Error: {e}")
        except (smtplib.SMTPException, OSError) as e:
            logger.error(f"Failed to send email to {recipient_email}. Error: {e}")
        return False
