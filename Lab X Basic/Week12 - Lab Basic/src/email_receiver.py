"""
email-sms-automator/src/email_receiver.py
Searches and reads emails over IMAP (SSL), decodes headers and saves attachments.
"""

import email
import imaplib
import os
from email import policy
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

try:
    from .utils import ensure_directory_exists, setup_logging
except ImportError:
    from utils import ensure_directory_exists, setup_logging

logger = setup_logging(__name__)


def _quote(value: str) -> str:
    """IMAP search values that contain spaces must be sent in double quotes."""
    return '"' + value.replace('\\', '').replace('"', '') + '"'


class EmailReceiver:
    """
    Reads emails via IMAP. Use it as a context manager so one connection is used for
    searching and fetching:

        with EmailReceiver(...) as receiver:
            for uid in receiver.search_emails(...):
                receiver.fetch_email_content(uid, ...)
    """

    def __init__(self, imap_server: str, sender_email: str, sender_password: str):
        self.imap_server = imap_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.mail = None

    # ------------------------------------------------------------ connection

    def connect(self, mailbox: str = 'INBOX') -> bool:
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.sender_email, self.sender_password)
            self.mail.select(mailbox)
            logger.info(f"Connected to IMAP server, mailbox '{mailbox}' selected.")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed - check SENDER_EMAIL and the App Password. Error: {e}")
        except OSError as e:
            logger.error(f"Could not connect to IMAP server '{self.imap_server}': {e}")
        self.mail = None
        return False

    def disconnect(self) -> None:
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.disconnect()

    # ---------------------------------------------------------------- search

    def search_emails(self, criteria: str = 'UNSEEN', from_sender: Optional[str] = None,
                      subject_contains: Optional[str] = None) -> List[str]:
        """Returns the UIDs of matching emails (empty list if not connected or nothing matches)."""
        if not self.mail:
            return []
        query = [criteria]
        if from_sender:
            query += ['FROM', _quote(from_sender)]
        if subject_contains:
            query += ['SUBJECT', _quote(subject_contains)]
        try:
            status, data = self.mail.uid('SEARCH', None, *query)
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP search failed: {e}")
            return []
        if status != 'OK':
            logger.error(f"IMAP search failed. Status: {status}")
            return []
        uids = [uid.decode() for uid in data[0].split()] if data and data[0] else []
        logger.info(f"Found {len(uids)} email(s) matching {' '.join(query)}.")
        return uids

    # ----------------------------------------------------------------- fetch

    def fetch_email_content(self, uid: str, mark_as_read: bool = True,
                            download_attachments_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetches one email by UID, optionally saving its attachments and marking it as read."""
        if not self.mail:
            return None
        try:
            # BODY.PEEK[] does not change the read flag; we set it ourselves below if asked
            status, data = self.mail.uid('FETCH', uid, '(BODY.PEEK[])')
            if status != 'OK' or not data or not isinstance(data[0], tuple):
                logger.error(f"Failed to fetch email UID {uid}. Status: {status}")
                return None
            return self._process_message(uid, data[0][1], mark_as_read, download_attachments_dir)
        except Exception as e:
            logger.error(f"Error fetching/parsing email UID {uid}: {e}")
            return None

    def _process_message(self, uid, raw_bytes, mark_as_read, download_attachments_dir):
        details = self.parse_message(raw_bytes, download_attachments_dir)
        details["uid"] = uid
        if mark_as_read:
            self.mail.uid('STORE', uid, '+FLAGS', '(\\Seen)')
            logger.info(f"Marked email UID {uid} as read.")
        return details

    @staticmethod
    def parse_message(raw_bytes: bytes, download_attachments_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses a raw email: decoded sender/subject (Thai text included), plain-text body and attachments.
        Attachments are saved under download_attachments_dir using only the file's base name.
        """
        msg = email.message_from_bytes(raw_bytes, policy=policy.default)
        body_part = msg.get_body(preferencelist=('plain', 'html'))
        body = body_part.get_content().strip() if body_part else ""

        saved = []
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if not filename or not download_attachments_dir:
                continue
            ensure_directory_exists(download_attachments_dir)
            safe_name = os.path.basename(filename)  # never trust paths inside attachment names
            path = os.path.join(download_attachments_dir, safe_name)
            with open(path, 'wb') as f:
                f.write(part.get_payload(decode=True))
            saved.append(path)
            logger.info(f"Downloaded attachment: {safe_name}")

        return {
            "sender": parseaddr(str(msg['From'] or ''))[1],
            "subject": str(msg['Subject'] or ''),
            "body_snippet": body[:200] + ("..." if len(body) > 200 else ""),
            "attachments_downloaded": saved,
        }
