# agentic-comm-automator/src/sms_tasks.py
from .utils import setup_logging

logger = setup_logging(__name__)

class SMSTasks:
    """
    Sends SMS through carrier email-to-SMS gateways (e.g. 1234567890@txt.att.net),
    using EmailTasks to deliver the message.
    """
    CARRIER_GATEWAYS = {
        "att": "@txt.att.net", "verizon": "@vtext.com", "tmobile": "@tmomail.net",
        "sprint": "@messaging.sprintpcs.com", "boost": "@sms.boostmobile.com",
        "uscellular": "@email.uscc.net", "cricket": "@sms.cricketwireless.net",
    }

    def __init__(self, email_tasks):
        self.email_tasks = email_tasks
        logger.info("SMSTasks initialized.")

    def gateway_address(self, phone_number, carrier_name=None):
        """Turns a phone number + carrier into a gateway email address (or uses an email address as-is)."""
        if "@" in phone_number:
            return phone_number
        if carrier_name and carrier_name.lower() in self.CARRIER_GATEWAYS:
            digits = "".join(ch for ch in phone_number if ch.isdigit())
            return f"{digits}{self.CARRIER_GATEWAYS[carrier_name.lower()]}"
        return None

    def send_sms(self, phone_numbers, message, carrier_name=None):
        """Sends `message` to every number. Returns (all_succeeded, list_of_gateway_addresses_used)."""
        sent_to = []
        for phone_number in phone_numbers:
            address = self.gateway_address(phone_number, carrier_name)
            if address is None:
                logger.warning(f"No SMS gateway for '{phone_number}' (carrier: {carrier_name!r}). Skipping.")
                continue
            # SMS gateways ignore the subject; keep it short so it does not eat into the 160 characters
            ok, _ = self.email_tasks.send_email({'to': [address]}, subject="SMS", body=message[:160])
            if ok:
                sent_to.append(address)
                logger.info(f"SMS sent to {phone_number} via {address}: '{message[:160]}'")
        return len(sent_to) == len(phone_numbers) and bool(phone_numbers), sent_to
