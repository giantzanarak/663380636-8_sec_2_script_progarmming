"""
Unit tests for the email/SMS automator. SMTP and IMAP are mocked - no real email is sent or read.
Run:  python -m unittest discover tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from email_receiver import EmailReceiver          # noqa: E402
from email_sender import EmailSender              # noqa: E402
from sms_gateway import SMSGateway                # noqa: E402

PDF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dummy_report.pdf")


class TestEmailSender(unittest.TestCase):

    def setUp(self):
        self.sender = EmailSender("smtp.test", 587, "me@test.com", "secret")

    def test_message_supports_thai_and_attachment(self):
        msg = self.sender.build_message("you@test.com", "ทดสอบ Subject", "นายภาวัต 663380636-8", PDF)
        self.assertEqual(msg["Subject"], "ทดสอบ Subject")
        self.assertIn("663380636-8", msg.get_body().get_content())
        self.assertEqual([p.get_filename() for p in msg.iter_attachments()], ["dummy_report.pdf"])

    def test_missing_attachment_is_skipped(self):
        msg = self.sender.build_message("you@test.com", "s", "b", "no_such_file.pdf")
        self.assertEqual(list(msg.iter_attachments()), [])

    @patch("email_sender.smtplib.SMTP")
    def test_send_uses_starttls_and_login(self, mock_smtp):
        server = mock_smtp.return_value.__enter__.return_value
        self.assertTrue(self.sender.send_email("you@test.com", "s", "b"))
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("me@test.com", "secret")
        server.send_message.assert_called_once()

    @patch("email_sender.smtplib.SMTP")
    def test_wrong_password_returns_false(self, mock_smtp):
        import smtplib
        mock_smtp.return_value.__enter__.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad")
        self.assertFalse(self.sender.send_email("you@test.com", "s", "b"))

    @patch("email_sender.smtplib.SMTP")
    def test_dry_run_sends_nothing(self, mock_smtp):
        dry = EmailSender("smtp.test", 587, "me@test.com", "secret", dry_run=True)
        self.assertTrue(dry.send_email("you@test.com", "s", "b"))
        mock_smtp.assert_not_called()


class TestSMSGateway(unittest.TestCase):

    def test_gateway_address(self):
        self.assertEqual(SMSGateway.gateway_address("123-456-7890", "ATT"), "1234567890@txt.att.net")
        self.assertEqual(SMSGateway.gateway_address("me@test.com"), "me@test.com")
        self.assertIsNone(SMSGateway.gateway_address("0812345678", ""), "no carrier -> no gateway")
        self.assertIsNone(SMSGateway.gateway_address("12345", "att"), "US gateways need 10 digits")

    def test_requires_email_sender(self):
        with self.assertRaises(TypeError):
            SMSGateway("not a sender")

    def test_send_sms_truncates_to_160_chars(self):
        sender = MagicMock(spec=EmailSender)
        sender.send_email.return_value = True
        self.assertTrue(SMSGateway(sender).send_sms("1234567890", "x" * 300, "verizon"))
        kwargs = sender.send_email.call_args.kwargs
        self.assertEqual(kwargs["recipient_email"], "1234567890@vtext.com")
        self.assertEqual(len(kwargs["body"]), 160)


class TestEmailReceiver(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_parse_message_decodes_thai_and_saves_attachment_safely(self):
        msg = EmailSender("s", 1, "me@test.com", "p").build_message(
            "me@test.com", "ทดสอบ Python Test", "นายภาวัต วงศ์มาลาสิทธิ์ 663380636-8", PDF)
        # an attacker-style file name must not escape the download folder
        for part in msg.iter_attachments():
            part.set_param("filename", "../../evil.pdf", header="Content-Disposition")
        details = EmailReceiver.parse_message(bytes(msg), self.tmp)
        self.assertEqual(details["subject"], "ทดสอบ Python Test")
        self.assertIn("663380636-8", details["body_snippet"])
        self.assertEqual(details["attachments_downloaded"], [os.path.join(self.tmp, "evil.pdf")])

    def test_search_quotes_values_with_spaces(self):
        receiver = EmailReceiver("imap.test", "me@test.com", "p")
        receiver.mail = MagicMock()
        receiver.mail.uid.return_value = ("OK", [b"11 12"])
        uids = receiver.search_emails("UNSEEN", "me@test.com", "Email for Receiving Demo")
        self.assertEqual(uids, ["11", "12"])
        args = receiver.mail.uid.call_args.args
        self.assertEqual(args[:2], ("SEARCH", None))
        self.assertIn('"Email for Receiving Demo"', args)

    def test_search_without_connection_returns_empty(self):
        self.assertEqual(EmailReceiver("imap.test", "a", "b").search_emails(), [])


if __name__ == "__main__":
    unittest.main()
