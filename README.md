# AI Customer Complaint & Case Processing System

A batch-oriented GenAI workflow that reads customer complaint documents from a
local folder and automatically produces structured case data, a customer
response email, and an internal case summary for each one — plus a
consolidated CSV report for management.

Built as the final project for the **IIT Patna USDC GenAI Development
Program** (Project 1: AI-Powered Document Processing & Business Workflow).

---

## 1. Problem Statement

Support teams receive complaint documents in different formats (plain text
notes, PDFs, Word forms) and currently have to read each one manually to:

- pull out the customer's details and the nature of the issue,
- draft a reply to the customer, and
- write an internal summary for the case tracker.

Doing this by hand for dozens of documents a day is slow and inconsistent.
This project automates all three steps using an LLM, while keeping a human
in the loop by producing everything as reviewable files rather than sending
anything automatically.

## 2. Solution Overview

The system treats each document as going through **three separate AI steps**
instead of one big prompt, so each step has one clear job and can be
inspected, tested, or improved independently:

1. **Structured Extraction** — the LLM reads the raw document text and
   returns a fixed set of fields (customer name, category, resolution
   status, etc.), which is validated against a Pydantic schema before it is
   trusted or saved.
2. **Customer Email Generation** — using only the validated data from step
   1, the LLM drafts a short, professional reply to the customer.
3. **Internal Case Summary** — again using only the validated data, the LLM
   writes a short internal summary (overview, key issue, action taken,
   status, recommended next step) for the operations team.

Multiple documents are processed **in parallel** (one worker thread per
document) since they are independent of each other, and the three steps
within a single document run **sequentially**, since step 2 and step 3 both
depend on step 1's output.

A failure on any single document (unreadable file, malformed LLM response)
is logged and skipped — it does not stop the rest of the batch.

## 3. Architecture

```
data/ folder (.txt, .pdf, .docx)
        │
        ▼
 Document Loader (document_loader.py)
        │
        ▼
 For each document (processed in parallel)
        │
        ▼
 Step 1: Structured Extraction (extractor.py)  ── LLM + Pydantic schema
        │
        ├──▶ Step 2: Customer Email (email_generator.py)
        │
        └──▶ Step 3: Internal Case Summary (summary_generator.py)
        │
        ▼
 output/structured_data/*.json, output/customer_emails/*.txt,
 output/case_summaries/*.txt
        │
        ▼
 Final Report Builder (report.py) ──▶ output/final_report.csv
```

See [`docs/architecture.png`](docs/architecture.png) for the diagram
(source: [`docs/architecture.mmd`](docs/architecture.mmd), Mermaid format).

## 4. Technology Stack

| Layer                  | Choice                                   |
|-------------------------|-------------------------------------------|
| Language                | Python 3.10+                             |
| LLM                     | OpenAI Chat Completions API (`gpt-4o-mini` by default) |
| Structured output       | Pydantic v2 models                       |
| Document parsing        | `pypdf` (PDF), `python-docx` (DOCX), built-in file I/O (TXT) |
| Batch/parallel execution| `concurrent.futures.ThreadPoolExecutor`  |
| Reporting               | `pandas` (CSV export)                    |
| Config / secrets        | `python-dotenv` (`.env` file)            |
| Logging                 | Python's built-in `logging` module       |

## 5. Project Structure

```
complaint-case-processor/
├── data/                        # Input complaint documents (sample data provided)
│   ├── complaint_001.txt
│   ├── complaint_002.pdf
│   ├── complaint_003.txt
│   ├── complaint_004.docx
│   └── complaint_005.txt
├── output/
│   ├── structured_data/         # One JSON per processed document
│   ├── customer_emails/         # One email .txt per processed document
│   ├── case_summaries/          # One internal summary .txt per processed document
│   └── final_report.csv         # Consolidated report across all documents
├── src/
│   ├── config.py                # Reads settings from environment variables
│   ├── document_loader.py       # Reads .txt / .pdf / .docx into plain text
│   ├── schema.py                # Pydantic models: ComplaintCase, CaseSummary
│   ├── llm_client.py            # Wrapper around the OpenAI API (+ mock mode)
│   ├── extractor.py             # Step 1: Structured Extraction
│   ├── email_generator.py       # Step 2: Customer Email
│   ├── summary_generator.py     # Step 3: Internal Case Summary
│   ├── workflow.py              # Orchestrates steps 1-3 across the batch
│   └── report.py                # Builds final_report.csv
├── tests/
│   └── test_schema_and_report.py
├── docs/
│   ├── architecture.mmd
│   └── architecture.png
├── main.py                      # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## 6. Setup Instructions

**Requirements:** Python 3.10 or later.

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd complaint-case-processor

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then open .env and paste in your own OPENAI_API_KEY
```

### Environment Variables

| Variable         | Required | Description                                                        |
|-------------------|----------|----------------------------------------------------------------------|
| `OPENAI_API_KEY`  | Yes*     | Your OpenAI API key. Get one at platform.openai.com/api-keys        |
| `OPENAI_MODEL`    | No       | Chat model to use. Defaults to `gpt-4o-mini`.                       |
| `MOCK_LLM`        | No       | Set to `true` to run the whole pipeline with a fake LLM response — useful for testing folder structure, error handling and the CSV report without spending API credits. Defaults to `false`. |
| `DATA_FOLDER`     | No       | Input folder. Defaults to `data`.                                  |
| `OUTPUT_FOLDER`   | No       | Output folder. Defaults to `output`.                                |
| `MAX_WORKERS`     | No       | Number of documents processed in parallel. Defaults to `4`.        |

\* Not required if `MOCK_LLM=true`.

**Never commit your real `.env` file.** It is already excluded via `.gitignore`.

## 7. How to Run

```bash
python main.py
```

This will:
1. Read every `.txt`, `.pdf` and `.docx` file in `data/`.
2. Run the 3-step AI workflow on each document (in parallel).
3. Write per-document outputs into `output/structured_data/`,
   `output/customer_emails/`, and `output/case_summaries/`.
4. Write a consolidated `output/final_report.csv`.
5. Write a full run log to `pipeline.log`.

To do a free, offline dry run first (no API key needed):

```bash
# in your .env file:
MOCK_LLM=true

python main.py
```

## 8. Sample Input

Five sample complaint documents are provided in `data/`, covering:

- a broadband speed complaint (`.txt`) requiring escalation,
- a delayed refund complaint (`.txt`),
- a missing-items delivery complaint (`.pdf`),
- an incorrect billing complaint (`.docx`),
- a piece of **positive feedback** (`.txt`) with no actual complaint, to
  verify the `is_complaint = "No"` path works correctly.

## 9. Sample Output

After a run, `output/final_report.csv` looks like:

| source_file | customer_name | complaint_category | is_complaint | escalation_required | overall_case_status | recommended_next_action |
|---|---|---|---|---|---|---|
| complaint_001.txt | Ananya Rao | Service Quality | Yes | Yes | Escalated | Assign to senior network engineer... |
| complaint_005.txt | Priya Nair | General | No | No | Resolved | No action needed... |

Each document also produces a JSON file (structured data), a `.txt` customer
email, and a `.txt` internal summary — see `output/` after running the
pipeline (or the mock-mode files already committed as an example, if
included).

## 10. Key Design Decisions

- **Three separate LLM calls instead of one big prompt.** This makes the
  workflow easier to debug (you can tell exactly which step failed), easier
  to test in isolation, and matches the "workflow orchestration" requirement
  rather than doing everything inside a single call.
- **Pydantic schema validation on every structured response.** The raw LLM
  output is never saved directly — it is parsed as JSON and validated
  against `ComplaintCase` / `CaseSummary` first, so malformed output is
  caught immediately instead of silently corrupting the report.
- **Parallel batch, sequential per-document steps.** Documents don't depend
  on each other, so they run concurrently via a thread pool. Within one
  document, email and summary generation both need the extracted data
  first, so those stay sequential.
- **A mock LLM mode.** `MOCK_LLM=true` lets the entire pipeline — file
  reading, error handling, folder structure, CSV generation — be tested
  without an API key or any cost, which was very useful during development.
- **Fail-soft batch processing.** One bad document (corrupt file, LLM
  returning invalid JSON) is logged and skipped rather than crashing the
  whole run.

## 11. Limitations

- Extraction quality depends on the underlying LLM and on how clearly the
  source document is written; very unusual document formats may need
  prompt adjustments.
- The customer email and case summary do not currently support any
  language other than English.
- Retries on LLM failures use a simple fixed backoff rather than a more
  advanced retry/rate-limit strategy.
- This is a local, single-machine batch tool — it does not include a web
  UI, database, or authentication, since those were out of scope for this
  assignment.
- PDF text extraction relies on the PDF containing selectable text; scanned
  image-only PDFs are not OCR'd.

## 12. Testing

Basic offline unit tests (no API key required) are included:

```bash
python -m pytest tests/ -v
```

These test the Pydantic schema validation and the CSV report builder.

---
*Built as part of the IIT Patna USDC GenAI Development Program.*
