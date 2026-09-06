"""
Workflow orchestration.

This is the piece that ties the three AI tasks together for a single
document, and then runs that per-document pipeline across the whole
batch. Each document goes through:

    1. Structured Extraction   (extractor.py)
    2. Customer Email          (email_generator.py)
    3. Internal Case Summary   (summary_generator.py)

Steps 2 and 3 both depend on step 1's output, so within one document the
three calls are sequential. Different documents are independent of each
other, so the batch is processed in parallel using a thread pool -- this
is safe here because each worker only does network calls (to the LLM
API) and writes to its own separate output files.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from src import config
from src.document_loader import load_documents_from_folder
from src.extractor import extract_structured_data
from src.email_generator import generate_customer_email
from src.summary_generator import generate_case_summary
from src.report import build_final_report
from src.schema import CaseSummary, ComplaintCase

logger = logging.getLogger(__name__)


def process_single_document(file_name: str, document_text: str, output_folder: str) -> Optional[dict]:
    """
    Run the full 3-step pipeline for one document and write its outputs
    to disk. Returns a dict with the case + summary objects on success,
    or None if this document failed (so the batch can continue).
    """
    try:
        logger.info("[%s] Step 1/3: extracting structured data", file_name)
        case = extract_structured_data(document_text, file_name)

        logger.info("[%s] Step 2/3: generating customer email", file_name)
        email_text = generate_customer_email(case)

        logger.info("[%s] Step 3/3: generating internal case summary", file_name)
        summary = generate_case_summary(case)

        _save_outputs(file_name, case, email_text, summary, output_folder)

        return {"case": case, "summary": summary}

    except Exception as exc:
        # A failure on one document (bad LLM output, schema mismatch,
        # API error after retries) should not stop the rest of the batch.
        logger.error("[%s] Failed to process document: %s", file_name, exc)
        return None


def _save_outputs(file_name: str, case: ComplaintCase, email_text: str, summary: CaseSummary, output_folder: str) -> None:
    stem = Path(file_name).stem
    output_root = Path(output_folder)

    structured_path = output_root / "structured_data" / f"{stem}.json"
    structured_path.write_text(case.model_dump_json(indent=2), encoding="utf-8")

    email_path = output_root / "customer_emails" / f"{stem}_email.txt"
    email_path.write_text(email_text, encoding="utf-8")

    summary_lines = (
        f"Case Overview: {summary.case_overview}\n"
        f"Key Issue: {summary.key_issue}\n"
        f"Action Taken: {summary.action_taken}\n"
        f"Current Status: {summary.current_status}\n"
        f"Recommended Next Action: {summary.recommended_next_action}\n"
    )
    summary_path = output_root / "case_summaries" / f"{stem}_summary.txt"
    summary_path.write_text(summary_lines, encoding="utf-8")


def run_batch(data_folder: str = None, output_folder: str = None) -> None:
    """
    Entry point for the whole pipeline: load every document, process the
    batch (in parallel), and write the consolidated final report.
    """
    data_folder = data_folder or config.DATA_FOLDER
    output_folder = output_folder or config.OUTPUT_FOLDER

    documents = load_documents_from_folder(data_folder)
    if not documents:
        logger.warning("No readable documents found in '%s'. Nothing to process.", data_folder)
        return

    logger.info("Loaded %d document(s). Starting batch processing with %d worker(s)...", len(documents), config.MAX_WORKERS)

    successful_cases: list[ComplaintCase] = []
    summaries_by_file: dict[str, CaseSummary] = {}

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        future_to_file = {
            executor.submit(process_single_document, file_name, text, output_folder): file_name
            for file_name, text in documents.items()
        }

        for future in as_completed(future_to_file):
            file_name = future_to_file[future]
            result = future.result()
            if result is not None:
                successful_cases.append(result["case"])
                summaries_by_file[file_name] = result["summary"]

    logger.info("Batch processing complete: %d/%d documents processed successfully.", len(successful_cases), len(documents))

    if successful_cases:
        build_final_report(successful_cases, summaries_by_file, output_folder)
    else:
        logger.warning("No documents were processed successfully; skipping final report.")
