"""
Step 1 of the workflow: Document -> Structured Extraction.

Sends the raw document text to the LLM and asks for a JSON object that
matches the ComplaintCase schema. The JSON is then validated with
Pydantic, so a badly-formed or incomplete response is caught here
instead of silently corrupting the final report.
"""

import json
import logging

from pydantic import ValidationError

from src.llm_client import call_llm
from src.schema import ComplaintCase

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an assistant that extracts structured data from customer \
complaint documents for a company's case management system.

Read the document text provided by the user and return ONLY a JSON object \
with exactly these fields:

- customer_name (string)
- email (string or null)
- phone_number (string or null)
- complaint_category (string, e.g. Billing, Product Defect, Delivery, Service Quality, Account Access)
- issue_description (string, one or two sentences)
- resolution_provided (string, use "None provided" if nothing was done yet)
- is_complaint ("Yes" or "No")
- escalation_required ("Yes" or "No")
- supporting_document_available ("Yes" or "No")
- overall_case_status ("Open", "In Progress", "Resolved", or "Escalated")

Only use information that is actually present in the document. Do not \
invent names, dates, or details. If a field is not mentioned, use null \
(for email/phone) or your best reasonable label based on context for the \
other fields. Return valid JSON only, with no extra commentary.
"""


def extract_structured_data(document_text: str, source_file: str) -> ComplaintCase:
    """
    Run the extraction LLM call for one document and return a validated
    ComplaintCase object.

    Raises pydantic.ValidationError if the model's response cannot be
    made to fit the schema even after one retry -- the caller (workflow.py)
    is responsible for catching that and logging the failed case.
    """
    user_prompt = f"Document ({source_file}):\n\n{document_text}"

    raw_response = call_llm(EXTRACTION_SYSTEM_PROMPT, user_prompt, json_mode=True)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        logger.error("Extractor got non-JSON response for %s: %s", source_file, exc)
        raise ValueError(f"LLM did not return valid JSON for {source_file}") from exc

    data["source_file"] = source_file

    try:
        case = ComplaintCase(**data)
    except ValidationError as exc:
        logger.error("Schema validation failed for %s: %s", source_file, exc)
        raise

    return case
