# agentic-comm-automator/src/communication_agent.py
import datetime
import json
import os
import time

from .utils import setup_logging, log_audit_entry, ensure_directory_exists
from .sms_tasks import SMSTasks
from .template_renderer import TemplateRenderer

logger = setup_logging(__name__)

class CommunicationAgent:
    """
    Runs the communication tasks from the config (send_email, send_sms, process_inbox).
    Templates are filled from `self.context`, and each task can store its result in the
    context (`output_context_key`) so later tasks can use it.
    """
    def __init__(self, config, base_dir, email_tasks, initial_context=None):
        self.config = config
        self.base_dir = base_dir
        self.email_tasks = email_tasks
        self.sms_tasks = SMSTasks(email_tasks)
        self.template_renderer = TemplateRenderer()
        self.audit_log = []
        self.context = dict(initial_context or {})
        self.start_time = datetime.datetime.now()

        # Task dispatcher: maps the task 'type' in the config to its handler method
        self.task_handlers = {
            "send_email": self._handle_send_email,
            "send_sms": self._handle_send_sms,
            "process_inbox": self._handle_process_inbox,
        }
        logger.info(f"CommunicationAgent initialized (mode: {email_tasks.mode}).")

    def _render(self, template_string, extra=None):
        return self.template_renderer.render(template_string, {**self.context, **(extra or {})})

    def _path(self, relative_path):
        return os.path.join(self.base_dir, relative_path)

    # --- Task handlers (return (success, output_for_context)) --------------------

    def _handle_send_email(self, params):
        recipients = {k: [self._render(r) for r in v] for k, v in params["recipients"].items()}
        subject = self._render(params["subject_template"])
        body = self._render(params["body_template"])
        attachments = [self._path(self._render(p)) for p in params.get("attachments", [])]
        return self.email_tasks.send_email(recipients, subject, body, attachments, params.get("is_html", False))

    def _handle_send_sms(self, params):
        numbers = [self._render(p) for p in params["phone_numbers"]]
        message = self._render(params["message_template"])
        ok, sent_to = self.sms_tasks.send_sms(numbers, message, params.get("carrier_name"))
        return ok, {"message": message, "sent_to": sent_to}

    @staticmethod
    def _rule_matches(conditions, email_info):
        """All conditions must hold. Text comparisons are case-insensitive."""
        text_checks = {"from_contains": "sender", "subject_contains": "subject", "body_contains": "text_body"}
        for key, field in text_checks.items():
            if key in conditions and conditions[key].lower() not in email_info[field].lower():
                return False
        if "has_attachments" in conditions and conditions["has_attachments"] != email_info["has_attachments"]:
            return False
        return True

    def _apply_rule_actions(self, actions, email_info, summary):
        """Runs the 'then' part of a matched rule and returns the names of the actions performed."""
        performed = []
        if actions.get("download_attachments_to"):
            saved = self.email_tasks.save_attachments(email_info, self._path(actions["download_attachments_to"]),
                                                      actions.get("allowed_extensions"))
            summary["attachments_downloaded"] += len(saved)
            performed.append(f"downloaded {len(saved)} attachment(s)")
        if actions.get("mark_as_read"):
            self.email_tasks.mark_as_read(email_info["uid"])
            summary["marked_as_read"] += 1
            performed.append("marked as read")
        if actions.get("send_sms_alert"):
            message = self._render(actions.get("alert_message_template", "Alert: {subject}"), email_info)
            numbers = [self._render(p) for p in actions.get("alert_phone_numbers", [])]
            ok, _ = self.sms_tasks.send_sms(numbers, message, actions.get("alert_carrier"))
            summary["sms_alerts_sent"] += int(ok)
            performed.append("SMS alert sent" if ok else "SMS alert FAILED")
        if actions.get("reply_with_template"):
            ok, _ = self.email_tasks.send_email(
                {'to': [email_info["sender"]]},
                self._render(actions.get("reply_subject_template", "Re: {subject}"), email_info),
                self._render(actions["reply_with_template"], email_info),
                in_reply_to=email_info["message_id"])
            summary["replies_sent"] += int(ok)
            performed.append("auto-reply sent" if ok else "auto-reply FAILED")
        return performed

    def _handle_process_inbox(self, params):
        criteria = params["search_criteria"]
        rules = params.get("rules", [])
        max_attempts = params.get("max_attempts", 3)
        retry_delay = params.get("retry_delay_seconds", 5)
        summary = {"processed_count": 0, "attachments_downloaded": 0, "marked_as_read": 0,
                   "sms_alerts_sent": 0, "replies_sent": 0, "emails": []}

        self.email_tasks.open_mailbox(params.get("mailbox", "INBOX"))
        try:
            # A just-sent email can take a few seconds to show up in the inbox, so retry the search
            uids = []
            for attempt in range(1, max_attempts + 1):
                uids = self.email_tasks.search_emails(criteria.get("status", "UNSEEN"),
                                                      criteria.get("from_sender"), criteria.get("subject_contains"))
                if uids or attempt == max_attempts:
                    break
                logger.info(f"No matching email yet (attempt {attempt}/{max_attempts}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

            for uid in uids:
                email_info = self.email_tasks.fetch_email(uid)
                actions_done = []
                for index, rule in enumerate(rules, start=1):
                    if self._rule_matches(rule["if"], email_info):
                        performed = self._apply_rule_actions(rule["then"], email_info, summary)
                        actions_done.append({"rule": rule.get("name", f"rule {index}"), "actions": performed})
                        log_audit_entry(self.audit_log, "INFO",
                                        f"Rule '{rule.get('name', index)}' matched email UID {uid}: {', '.join(performed)}",
                                        "process_inbox", {"subject": email_info["subject"]})
                summary["processed_count"] += 1
                summary["emails"].append({"uid": uid, "from": email_info["sender"],
                                          "subject": email_info["subject"], "rules": actions_done})
        finally:
            self.email_tasks.close_mailbox()

        if not uids:
            log_audit_entry(self.audit_log, "WARNING", "No emails matched the search criteria.", "process_inbox", criteria)
        return True, summary

    # -------------------------------------------------------------------------------

    def _process_task(self, task):
        task_type = task.get("type")
        task_name = task.get("name", task_type)
        output_context_key = task.get("output_context_key")

        logger.info(f"Executing task: '{task_name}' (Type: {task_type})")
        log_audit_entry(self.audit_log, "INFO", f"Starting task '{task_name}'", task_type)

        handler = self.task_handlers.get(task_type)
        if handler is None:
            log_audit_entry(self.audit_log, "WARNING", f"Unsupported task type: {task_type}", task_type)
            return False
        try:
            success, output = handler(task.get("parameters", {}))
        except Exception as e:
            log_audit_entry(self.audit_log, "ERROR", f"An error occurred during task '{task_name}': {e}",
                            task_type, {"error": str(e)})
            logger.debug("Task error details", exc_info=True)
            return False

        if success and output_context_key:
            self.context[output_context_key] = output
        details = {k: v for k, v in (output or {}).items() if k != "emails"}
        log_audit_entry(self.audit_log, "SUCCESS" if success else "ERROR",
                        f"Task '{task_name}' {'completed' if success else 'failed'}.", task_type, details)
        return success

    def _generate_audit_report(self, output_dir):
        ensure_directory_exists(output_dir)
        report_path = os.path.join(output_dir, f"audit_report_comm_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({"mode": self.email_tasks.mode, "context": self.context, "audit_log": self.audit_log},
                          f, indent=4, ensure_ascii=False, default=str)
            logger.info(f"Audit report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}")

    def run(self):
        logger.info("Starting Communication Agent run...")
        log_audit_entry(self.audit_log, "INFO", f"Communication Agent started (mode: {self.email_tasks.mode}).", "agent_run")

        tasks = self.config.get("tasks", [])
        succeeded = sum(1 for task in tasks if self._process_task(task))

        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        log_audit_entry(self.audit_log, "INFO", f"Finished {succeeded}/{len(tasks)} tasks successfully in {duration:.2f}s.",
                        "agent_run_summary")
        self._generate_audit_report(self._path("reports"))
        return succeeded == len(tasks)
