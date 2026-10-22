# agentic-comm-automator/src/email_tasks.py
import email
import imaplib
import json
import mimetypes
import os
import re
import smtplib
from email import policy
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

from .utils import setup_logging, ensure_directory_exists

logger = setup_logging(__name__)

class EmailTasks:
    """
    Sends email over SMTP and reads the inbox over IMAP (live mode, e.g. Gmail).
    Message building and parsing live here too, so MockEmailTasks can reuse them.
    """
    mode = "live"

    def __init__(self, smtp_server, smtp_port, imap_server, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self._imap = None
        logger.info(f"EmailTasks initialized for {sender_email} (mode: {self.mode}).")

    # --- Sending --------------------------------------------------------------

    def build_message(self, recipients, subject, body, attachments=None, is_html=False, in_reply_to=None):
        """Builds an EmailMessage with To/Cc, plain text (+ optional HTML) body and attachments."""
        msg = EmailMessage()
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(recipients.get('to', []))
        if recipients.get('cc'):
            msg['Cc'] = ", ".join(recipients['cc'])
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain="agentic-comm-automator.local")
        if in_reply_to:
            msg['In-Reply-To'] = in_reply_to
            msg['References'] = in_reply_to

        if is_html:
            # Plain-text fallback for clients that do not show HTML
            msg.set_content(re.sub(r"<[^>]+>", "", body))
            msg.add_alternative(body, subtype='html')
        else:
            msg.set_content(body)

        attached = []
        for attachment_path in attachments or []:
            if not os.path.exists(attachment_path):
                logger.warning(f"Attachment file not found: {attachment_path}. Skipping.")
                continue
            content_type, _ = mimetypes.guess_type(attachment_path)
            maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
            with open(attachment_path, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                                   filename=os.path.basename(attachment_path))
            attached.append(os.path.basename(attachment_path))
        return msg, attached

    def send_email(self, recipients, subject, body, attachments=None, is_html=False, in_reply_to=None):
        """Sends an email to To/Cc/Bcc recipients. Returns (success, info_dict)."""
        # dict.fromkeys removes duplicates (e.g. the same address in To and Cc) but keeps the order
        all_recipients = list(dict.fromkeys(recipients.get('to', []) + recipients.get('cc', []) + recipients.get('bcc', [])))
        if not all_recipients:
            logger.error("No recipients specified for email.")
            return False, {}

        msg, attached = self.build_message(recipients, subject, body, attachments, is_html, in_reply_to)
        try:
            self._deliver(msg, all_recipients)
        except Exception as e:
            logger.error(f"Failed to send email '{subject}': {e}")
            return False, {}

        logger.info(f"Email sent to {', '.join(all_recipients)}. Subject: '{subject}'. Attachments: {attached or 'none'}.")
        return True, {"to": all_recipients, "subject": subject, "attachments": attached}

    def _deliver(self, msg, all_recipients):
        """Sends a built message through the SMTP server (STARTTLS + login)."""
        with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg, from_addr=self.sender_email, to_addrs=all_recipients)

    # --- Receiving (IMAP) -------------------------------------------------------

    def open_mailbox(self, mailbox="INBOX"):
        self._imap = imaplib.IMAP4_SSL(self.imap_server)
        self._imap.login(self.sender_email, self.sender_password)
        self._imap.select(mailbox)
        logger.info(f"Connected to IMAP server, mailbox '{mailbox}' selected.")

    def close_mailbox(self):
        if self._imap:
            try:
                self._imap.logout()
            except Exception:
                pass
            self._imap = None

    @staticmethod
    def _quote(value):
        return '"' + value.replace('"', '') + '"'

    def search_emails(self, status="UNSEEN", from_sender=None, subject_contains=None):
        """Returns the UIDs of emails that match the status and optional sender/subject filters."""
        query = [status]
        if from_sender:
            query += ['FROM', self._quote(from_sender)]
        if subject_contains:
            query += ['SUBJECT', self._quote(subject_contains)]
        result, data = self._imap.uid('SEARCH', None, *query)
        if result != 'OK':
            logger.error(f"IMAP search failed: {result}")
            return []
        uids = [uid.decode() for uid in data[0].split()]
        logger.info(f"Found {len(uids)} email(s) matching {' '.join(query)}.")
        return uids

    def _fetch_raw(self, uid):
        # BODY.PEEK[] does not mark the email as read; that is decided by the rules
        result, data = self._imap.uid('FETCH', uid, '(BODY.PEEK[])')
        if result != 'OK' or not data or not isinstance(data[0], tuple):
            raise RuntimeError(f"Could not fetch email UID {uid}")
        return data[0][1]

    def mark_as_read(self, uid):
        self._imap.uid('STORE', uid, '+FLAGS', '(\\Seen)')
        logger.info(f"Email UID {uid} marked as read.")

    # --- Parsing / attachments (shared by live and mock) ------------------------

    def fetch_email(self, uid):
        """Fetches and parses an email. Returns a dict usable as template context."""
        msg = email.message_from_bytes(self._fetch_raw(uid), policy=policy.default)
        body_part = msg.get_body(preferencelist=('plain', 'html'))
        text_body = body_part.get_content() if body_part else ""
        attachments = [{"filename": part.get_filename(), "content": part.get_payload(decode=True)}
                       for part in msg.iter_attachments() if part.get_filename()]
        sender_name, sender_address = parseaddr(str(msg['From'] or ""))
        info = {
            "uid": uid,
            "sender": sender_address,
            "sender_name": sender_name or sender_address,
            "subject": str(msg['Subject'] or ""),
            "message_id": str(msg['Message-ID'] or ""),
            "text_body": text_body,
            "has_attachments": bool(attachments),
            "attachment_names": ", ".join(a["filename"] for a in attachments) or "none",
            "_attachments": attachments,
        }
        logger.info(f"Fetched email UID {uid} from {info['sender']}: '{info['subject']}' ({len(attachments)} attachment(s)).")
        return info

    @staticmethod
    def save_attachments(email_info, target_dir, allowed_extensions=None):
        """Saves the email's attachments (optionally only some file types). Returns saved paths."""
        ensure_directory_exists(target_dir)
        saved = []
        for attachment in email_info.get("_attachments", []):
            filename = os.path.basename(attachment["filename"]) # never trust paths inside attachment names
            if allowed_extensions and os.path.splitext(filename)[1].lower() not in allowed_extensions:
                logger.info(f"Skipping attachment '{filename}' (type not allowed).")
                continue
            path = os.path.join(target_dir, filename)
            with open(path, "wb") as f:
                f.write(attachment["content"])
            saved.append(path)
            logger.info(f"Downloaded attachment: {path}")
        return saved


class MockEmailTasks(EmailTasks):
    """
    Offline stand-in for SMTP/IMAP so the whole workflow can run without an email account.
    - Every sent email is saved as a .eml file in data/outbox/ (double-click to open in Mail).
    - Emails addressed to SENDER_EMAIL are also delivered to data/mock_mailbox/, which
      process_inbox reads like an IMAP inbox (read/unread flags kept in flags.json).
    """
    mode = "mock"

    def __init__(self, sender_email, data_dir):
        self.outbox_dir = os.path.join(data_dir, "outbox")
        self.mailbox_dir = os.path.join(data_dir, "mock_mailbox")
        self.flags_path = os.path.join(self.mailbox_dir, "flags.json")
        ensure_directory_exists(self.outbox_dir)
        ensure_directory_exists(self.mailbox_dir)
        super().__init__(None, None, None, sender_email, None)

    def _load_flags(self):
        if os.path.exists(self.flags_path):
            with open(self.flags_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_flags(self, flags):
        with open(self.flags_path, "w", encoding="utf-8") as f:
            json.dump(flags, f, indent=2)

    def _deliver(self, msg, all_recipients):
        flags = self._load_flags()
        sequence = len(os.listdir(self.outbox_dir)) + 1
        safe_subject = re.sub(r"[^A-Za-z0-9]+", "_", str(msg['Subject']))[:50].strip("_") or "no_subject"
        with open(os.path.join(self.outbox_dir, f"{sequence:03d}_{safe_subject}.eml"), "wb") as f:
            f.write(bytes(msg))
        if self.sender_email.lower() in (r.lower() for r in all_recipients):
            uid = str(len(flags) + 1)
            with open(os.path.join(self.mailbox_dir, f"{uid}.eml"), "wb") as f:
                f.write(bytes(msg))
            flags[uid] = {"seen": False}
            self._save_flags(flags)

    def open_mailbox(self, mailbox="INBOX"):
        logger.info(f"Opened mock mailbox '{mailbox}' at {self.mailbox_dir}.")

    def close_mailbox(self):
        pass

    def search_emails(self, status="UNSEEN", from_sender=None, subject_contains=None):
        flags = self._load_flags()
        uids = []
        for uid, flag in flags.items():
            if status == "UNSEEN" and flag["seen"]:
                continue
            msg = email.message_from_bytes(self._fetch_raw(uid), policy=policy.default)
            # IMAP FROM / SUBJECT searches are case-insensitive substring matches
            if from_sender and from_sender.lower() not in str(msg['From']).lower():
                continue
            if subject_contains and subject_contains.lower() not in str(msg['Subject']).lower():
                continue
            uids.append(uid)
        logger.info(f"Found {len(uids)} email(s) in mock mailbox matching status={status}, "
                    f"from={from_sender}, subject~={subject_contains}.")
        return uids

    def _fetch_raw(self, uid):
        with open(os.path.join(self.mailbox_dir, f"{uid}.eml"), "rb") as f:
            return f.read()

    def mark_as_read(self, uid):
        flags = self._load_flags()
        flags[uid]["seen"] = True
        self._save_flags(flags)
        logger.info(f"Email UID {uid} marked as read.")
