# Step-by-Step Code Walkthrough

This is a plain-language guide to every file in `src/`, written so you can
explain the project confidently during the live evaluation. Read it in this
order — it follows the actual flow of data through the program.

---

## 1. `main.py` — the entry point

When you run `python main.py`, this file:
1. Sets up logging (prints to the screen **and** writes to `pipeline.log`).
2. Calls `run_batch()` from `src/workflow.py`.
3. Prints a final "Done" message.

If you're asked "how do I run this?" — the answer is this file.

## 2. `src/config.py` — settings in one place

Reads everything that can change between machines (API key, model name,
folder paths, worker count) from environment variables (from your `.env`
file). Nothing is hard-coded elsewhere in the project — if the evaluator
asks "what if I want to use a different model?", the answer is: change
`OPENAI_MODEL` in `.env`, no code changes needed.

`MOCK_LLM` is worth explaining if asked: it's a boolean flag that lets the
*entire* pipeline run without calling the real API at all, useful for
testing the file-handling and reporting logic for free.

## 3. `src/document_loader.py` — turning files into text

Three small functions (`read_txt`, `read_pdf`, `read_docx`) each know how
to pull plain text out of one file type. `load_document_text()` picks the
right one based on the file extension, and wraps it in a `try/except` so a
single corrupt or unreadable file returns `None` instead of crashing the
whole program — that's the "handle file-level errors gracefully"
requirement.

`load_documents_from_folder()` loops over every file in `data/`, skips
anything that isn't `.txt`/`.pdf`/`.docx`, and returns a dictionary of
`{filename: text}` for everything it could read.

**If asked "how do you support multiple formats?"** — point here.

## 4. `src/schema.py` — the contract for LLM output

Two Pydantic classes:

- `ComplaintCase` — the exact fields Step 1 must produce (customer name,
  category, escalation flag, etc.), each with a `Field(description=...)`
  that doubles as documentation and as part of what gets sent to the LLM.
- `CaseSummary` — the fields Step 3 must produce.

Pydantic's job here is to **reject** anything that doesn't match this
shape — wrong type, missing field, or a value outside the allowed set (for
example `overall_case_status` can only be one of four specific strings).
This is what the assignment means by "the output should follow a defined
schema... the application should not simply save the raw LLM response."

**If asked "why Pydantic instead of just using the JSON directly?"** — this
is the answer: it's the difference between trusting the LLM blindly and
validating what it gives you before you save or act on it.

## 5. `src/llm_client.py` — the one place that talks to OpenAI

Every other module calls `call_llm(system_prompt, user_prompt, json_mode)`
instead of importing the OpenAI SDK directly. Benefits, if asked:
- One place to change the API key/model.
- One place to add retry logic (it retries up to 2 extra times with a
  short backoff if the API call fails).
- One place to redirect to a mock response when `MOCK_LLM=true`.

`json_mode=True` tells OpenAI to constrain its output to valid JSON
(`response_format={"type": "json_object"}`) — this is what makes the
schema validation step in `extractor.py` and `summary_generator.py`
reliable.

## 6. `src/extractor.py` — Step 1: Structured Extraction

1. Builds a prompt telling the LLM exactly which fields to return and to
   only use information actually present in the document (this is the
   "avoid inventing information" requirement).
2. Calls `call_llm(..., json_mode=True)`.
3. Parses the response with `json.loads()`.
4. Validates it into a `ComplaintCase` object.

If step 3 or 4 fails (bad JSON, or JSON that doesn't match the schema), it
raises an error, which `workflow.py` catches so that one bad document
doesn't stop the batch.

## 7. `src/email_generator.py` — Step 2: Customer Email

Takes the **validated** `ComplaintCase` from Step 1 (not the raw document)
and asks the LLM to draft a short, professional reply. Notice the prompt
explicitly says "do not invent any new facts" — that's the guardrail
against hallucination for this step.

This step deliberately does **not** re-read the original document — it
only sees the structured fields, which keeps its output grounded in what
was already extracted and validated.

## 8. `src/summary_generator.py` — Step 3: Internal Case Summary

Same pattern as email generation, but the prompt is written for an
internal/management audience and returns structured JSON (`CaseSummary`)
instead of free text, since the summary has clearly defined sub-fields
(overview, key issue, action taken, status, next action).

## 9. `src/workflow.py` — tying it all together

Two important functions:

- `process_single_document()` — runs Steps 1 → 2 → 3 **in that order**
  for one document (they must be sequential because 2 and 3 both need
  Step 1's output), saves the three output files, and catches any
  exception so a failure here doesn't kill the batch.
- `run_batch()` — loads all documents, then uses
  `ThreadPoolExecutor` to process **multiple documents at the same time**
  (this is the "batch/parallel processing" requirement — documents don't
  depend on each other, so this is safe), then calls `build_final_report()`.

**If asked "where is the workflow orchestration?"** — this file is the
answer. It's deliberately not one giant LLM call; it's three small,
single-purpose calls chained together with real Python control flow.

## 10. `src/report.py` — the consolidated view

Takes the list of successful `ComplaintCase` objects plus their matching
`CaseSummary` objects, builds a table with `pandas`, and writes
`output/final_report.csv`.

---

## Things you should be ready to explain live

1. **Why three LLM calls instead of one?** Single responsibility per
   call, easier debugging, matches the "workflow orchestration" grading
   criterion, and means a bad output in one step doesn't affect the
   others.
2. **Where does structured output / Pydantic get enforced?** In
   `schema.py` (the models) and in `extractor.py` / `summary_generator.py`
   (where `ComplaintCase(**data)` / `CaseSummary(**data)` will raise if the
   data doesn't fit).
3. **How is batch processing implemented?** `ThreadPoolExecutor` in
   `workflow.py`, `MAX_WORKERS` configurable via `.env`.
4. **How are errors handled?** Two layers: `document_loader.py` catches
   file-read errors per file, and `workflow.py` catches any exception per
   document during LLM processing — both log and continue rather than
   crash.
5. **How would you test this without spending API credits?** `MOCK_LLM=true`
   in `.env`, plus the offline unit tests in `tests/`.
