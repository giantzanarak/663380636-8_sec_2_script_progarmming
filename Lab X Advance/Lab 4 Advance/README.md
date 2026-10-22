# Week 11 LabX ADV: Project Planning & Design - Building an Enhanced Task Manager

An **Agentic Document Automator** for the Enhanced Task Manager project. A `DocumentAgent`
reads `configs/document_automation_config.json` and runs each task in order:
generating a Word report from a template, watermarking a PDF, merging PDFs and extracting
text, then writes an audit report of every step.

Video: https://drive.google.com/file/d/1NnSoPx1C3hzNyUBZ_pJvpC1OqFJ2I6rQ/view?usp=sharing

## Results (screenshots)

### `documents/merged_docs.pdf`
![merged_docs.pdf](screenshots/merged_docs.png)

### `documents/generated_report.docx`
![generated_report.docx](screenshots/generated_report.png)

### `documents/watermarked_document.pdf`
![watermarked_document.pdf](screenshots/watermarked_document.png)

## Agent tasks

| # | Task | Type | Input → Output |
|---|------|------|----------------|
| 1 | Generate Monthly Performance Report | `generate_word_report` | `templates/report_template.docx` → `documents/generated_report.docx` |
| 2 | Apply Confidential Watermark to PDF | `apply_pdf_watermark` | `documents/source_document.pdf` → `documents/watermarked_document.pdf` |
| 3 | Merge Project Documentation | `merge_pdfs` | `dummy_doc1.pdf` + `dummy_doc2.pdf` → `documents/merged_docs.pdf` |
| 4 | Extract Text from Generated Word Report | `extract_word_text` | `generated_report.docx` → `documents/extracted_word_text.txt` |
| 5 | Extract Text from Source PDF | `extract_pdf_text` | `source_document.pdf` → `documents/extracted_pdf_text.txt` |

The audit report is saved to `documents/reports/audit_report_<timestamp>.json`.

### How the Word template works
`templates/report_template.docx` contains fields like `{{REPORT_TITLE}}`, `{{MONTH_PERIOD}}`, `{{AUTHOR_NAME}}`.
The agent combines `global_data` with the task's `data` (task values win) and replaces each field,
including fields in the footer. The rows in `table_data` become a table inserted exactly where
`{{TABLE_PLACEHOLDER}}` is in the template.

## How to Run

```bash
cd "Lab X Advance/Lab 4 Advance"
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python create_sample_files.py     # creates the Word template and the input PDFs
python main.py                    # runs the Document Agent
```

## Project Structure

```
agentic-document-automator/
├── src/
│   ├── __init__.py
│   ├── document_agent.py   # DocumentAgent: task dispatcher + audit report
│   ├── word_tasks.py       # fill Word template, insert table, extract Word text
│   ├── pdf_tasks.py        # watermark, merge, extract PDF text
│   ├── config_parser.py    # loads and validates the JSON config
│   └── utils.py            # logging, directory helper, audit log entries
├── configs/
│   └── document_automation_config.json
├── templates/
│   └── report_template.docx
├── documents/
│   ├── source_document.pdf, dummy_doc1.pdf, dummy_doc2.pdf   # inputs
│   ├── generated_report.docx                                 # output
│   ├── watermarked_document.pdf                              # output
│   ├── merged_docs.pdf                                       # output
│   ├── extracted_word_text.txt, extracted_pdf_text.txt       # output
│   └── reports/audit_report_*.json
├── screenshots/
├── create_sample_files.py
├── main.py
├── requirements.txt
└── README.md
```

## Improvements over the example code

* **Placeholders are fully replaced.** The example replaced `REPORT_TITLE` inside `{{REPORT_TITLE}}`, leaving
  `{{Monthly Performance Summary}}` in the report. The agent now replaces the whole `{{KEY}}`, also when Word splits
  it across several runs, and also in headers/footers. Leftover placeholders are logged as a warning.
* **The table goes where `{{TABLE_PLACEHOLDER}}` is**, not at the end of the document after the conclusion.
* **Watermark** is built in memory at each page's own size (no temporary file), so it is centred on any page format.
* **`create_sample_files.py`** recreates the template and input PDFs, so the project runs from a fresh clone.
* `requirements.txt` lists the dependencies (`python-docx`, `pypdf`, `reportlab`). `pypdf` is the maintained successor of `PyPDF2` with the same API.
* The config parser checks the required fields of every task type, `main.py` checks that all input files exist
  before running, and the agent uses a dispatcher dictionary instead of an `if/elif` chain.
