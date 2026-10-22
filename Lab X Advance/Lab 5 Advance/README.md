# Week 12 LabX ADV: Agentic Communication Workflows (Advanced Email & SMS)

A configuration-driven **CommunicationAgent** that sends templated emails and SMS, then reads the
inbox and reacts to incoming emails with "if → then" rules (download attachments, mark as read,
SMS alert, auto-reply). All tasks are defined in `configs/comm_pipeline_config.json`.

Video: https://drive.google.com/file/d/1IQG5n4ZtnCZXstkHJfyGHwmwLuJx7XBq/view?usp=sharing

## Results (screenshots)

### Terminal output (`python main.py`)
![Terminal output](screenshots/terminal.png)

### Inbox after the run
![Inbox](screenshots/inbox.png)

### Downloaded attachment + audit report
![Incoming attachments and audit report](screenshots/attachments_audit.png)

## Workflow

| # | Task | Type | What happens |
|---|------|------|--------------|
| 1 | Send Daily Sales Report Email | `send_email` | HTML email (To + Cc) with `sales_report.pdf` and `summary_data.xlsx` attached; subject/body filled from the context |
| 2 | Send Sales Summary SMS | `send_sms` | Short message via an email-to-SMS gateway, using data from task 1 (`{report_email[to][0]}`) |
| 3 | Simulate Incoming Request Email | `send_email` | Sends "Data Request for <date> - Urgent" with a PDF to yourself |
| 4 | Process Incoming Data Requests | `process_inbox` | Searches UNSEEN emails from you with "Data Request" in the subject (retries while the email arrives) and applies the rules below |
| 5 | Send Workflow Summary Email | `send_email` | Reports what tasks 1–4 did, using values the agent stored in its context |

**Inbox rules (task 4)**

| Rule | If | Then |
|------|----|------|
| Save request attachments | sender is me **and** subject contains "Request" | save attachments (`.pdf/.xlsx/.csv` only) to `data/incoming_attachments/`, mark as read |
| Urgent SMS alert | body contains "urgent" | send an SMS alert with sender, subject and attachment names |
| Auto-reply to data requests | body contains "new data processing" | reply to the sender with a templated message |

**Context passing:** every task can save its result with `output_context_key`
(`report_email`, `sales_sms`, `inbox_result`), and later templates read it, e.g.
`{inbox_result[attachments_downloaded]}`. Config values like `${SENDER_EMAIL}` come from `.env`.

Every step is written to `reports/audit_report_comm_<timestamp>.json` (together with the final context).

## Two modes

| Mode | When | Email | Inbox |
|------|------|-------|-------|
| **live** | `.env` has a real `SENDER_EMAIL` + `SENDER_APP_PASSWORD` (or `python main.py --live`) | Gmail SMTP | Gmail IMAP |
| **mock** | no credentials (or `python main.py --mock`) | saved as `.eml` in `data/outbox/` (double-click to open in Mail) | `data/mock_mailbox/` |

Mock mode runs the exact same agent, templates and rules without an email account, which is handy
for testing the workflow before using a real mailbox.

## Setup & How to Run

```bash
cd "Lab X Advance/Lab 5 Advance"
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_sample_files.py     # creates data/reports/sales_report.pdf and summary_data.xlsx
cp .env.example .env              # then edit .env (see below)
python main.py
```

### Gmail setup for live mode
1. Turn on **2-Step Verification** for your Google account.
2. Google Account → Security → **App passwords** → create one (16 characters).
3. In `.env` set `SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `TEST_RECIPIENT_EMAIL` (can be your own address)
   and `TEST_SMS_PHONE_NUMBER`.
4. `.env` is in `.gitignore` - never commit it.

> **SMS:** email-to-SMS gateways only exist for some (mostly US) carriers, e.g. `1234567890` + carrier
> `att` → `1234567890@txt.att.net`. Thai carriers have no such gateway, so set `TEST_SMS_PHONE_NUMBER`
> to an email address and leave `TEST_SMS_CARRIER` empty; the "SMS" then arrives as a short email.

## Project Structure

```
agentic-comm-automator/
├── src/
│   ├── __init__.py
│   ├── communication_agent.py  # agent: task dispatcher, context, inbox rule engine, audit report
│   ├── email_tasks.py          # EmailTasks (SMTP/IMAP) + MockEmailTasks (offline)
│   ├── sms_tasks.py            # SMS through email-to-SMS gateways
│   ├── template_renderer.py    # "{key}" / "{value:,.2f}" / "{dict[key]}" templates
│   ├── config_parser.py        # loads config, replaces ${ENV_VAR}, validates tasks
│   └── utils.py                # logging, .env loading, audit log entries
├── configs/
│   └── comm_pipeline_config.json
├── data/
│   ├── reports/                # sample attachments (from create_sample_files.py)
│   └── incoming_attachments/   # attachments downloaded by the inbox rules
├── reports/                    # audit_report_comm_*.json
├── screenshots/
├── create_sample_files.py
├── main.py
├── .env.example
├── requirements.txt
└── README.md
```

## Troubleshooting

* **`SMTPAuthenticationError` / IMAP login failed:** use an App Password, not your normal password, and check `SENDER_EMAIL`.
* **"No emails matched the search criteria":** Gmail can take a few seconds to deliver; the agent retries
  (`max_attempts`, `retry_delay_seconds`). Also check the email is still unread.
* **`Missing context key`:** a template uses `{name}` that is not in the context or the email being processed.

## Improvements over the example code

* Imports work as a package (`from src...`); config values like `${SENDER_EMAIL}` are actually replaced from `.env`.
* IMAP uses real **UIDs** with one connection per inbox task, quotes search terms with spaces (`"Data Request"`),
  and fetches with `BODY.PEEK[]`, so only the `mark_as_read` rule marks emails as read.
* Rules are configurable actions (`download_attachments_to` + `allowed_extensions`, `mark_as_read`, `send_sms_alert`,
  `reply_with_template`), matched case-insensitively; replies keep the thread with `In-Reply-To`.
* HTML emails include a plain-text fallback; duplicate recipients (same address in To and Cc) are sent once.
* Attachment filenames are reduced to their base name before saving (no path tricks from incoming email).
* One failing task no longer stops the run, and the audit report includes the final context.
* Offline **mock mode** for running without an email account.
