"""
email-sms-automator/src/sms_gateway.py
Sends SMS text messages through carrier email-to-SMS gateways.
"""

from typing import Optional

try:
    from .email_sender import EmailSender
    from .utils import setup_logging
except ImportError:
    from email_sender import EmailSender
    from utils import setup_logging

logger = setup_logging(__name__)

# Common US carrier email-to-SMS gateways
CARRIER_GATEWAYS = {
    "att": "@txt.att.net",
    "verizon": "@vtext.com",
    "tmobile": "@tmomail.net",
    "sprint": "@messaging.sprintpcs.com",
    "boost": "@sms.boostmobile.com",
    "cricket": "@mms.cricketwireless.net",
    "us_cellular": "@email.uscc.net",
}


class SMSGateway:
    """Turns a phone number + carrier into a gateway address and sends the text with EmailSender."""

    def __init__(self, email_sender_instance: EmailSender):
        if not isinstance(email_sender_instance, EmailSender):
            raise TypeError("SMSGateway requires an instance of EmailSender.")
        self.email_sender = email_sender_instance

    @staticmethod
    def gateway_address(phone_number: str, carrier_name: Optional[str] = None) -> Optional[str]:
        """Returns the gateway email address, or None if it cannot be determined."""
        phone_number = phone_number.strip()
        if "@" in phone_number:
            return phone_number  # already an address (e.g. your own email for testing)
        if carrier_name and carrier_name.strip().lower() in CARRIER_GATEWAYS:
            digits = "".join(ch for ch in phone_number if ch.isdigit())
            if len(digits) == 10:
                return digits + CARRIER_GATEWAYS[carrier_name.strip().lower()]
            logger.warning(f"Phone number '{phone_number}' must have 10 digits for a US gateway.")
        return None

    def send_sms(self, phone_number: str, message: str, carrier_name: Optional[str] = None) -> bool:
        """Sends an SMS (max 160 characters). Returns True if the gateway email was sent."""
        address = self.gateway_address(phone_number, carrier_name)
        if address is None:
            logger.warning("No SMS gateway for this number/carrier - SMS not sent. "
                           "(Thai carriers have no email-to-SMS gateway.)")
            return False
        logger.info(f"Sending SMS to {phone_number} via gateway: {address}")
        # Gateways ignore the subject; keep the text within one SMS
        return self.email_sender.send_email(recipient_email=address, subject="SMS", body=message[:160])
