"""
Step 3 of the workflow: Extracted Data -> Internal Case Summary.

Generates a short, internal-facing summary for the management/ops team,
covering the case overview, key issue, action taken so far, current
status, and a recommended next action.
"""

import json
import logging

from pydantic import ValidationError

from src.llm_client import call_llm
from src.schema import CaseSummary, ComplaintCase

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """You are writing an internal case summary for a company's operations \
and management team (not for the customer).

Return ONLY a JSON object with exactly these fields:
- case_overview (1-2 sentences, factual)
- key_issue (1 sentence)
- action_taken (1 sentence, use "None yet" if nothing has been done)
- current_status (1 short phrase)
- recommended_next_action (1 sentence, a practical next step for the team)

Base everything only on the case data you are given. Do not invent \
details that are not present.
"""


def generate_case_summary(case: ComplaintCase) -> CaseSummary:
    """Generate an internal management summary for one processed case."""
    user_prompt = f"""Case data:

Customer Name: {case.customer_name}
Complaint Category: {case.complaint_category}
Issue Description: {case.issue_description}
Resolution Provided: {case.resolution_provided}
Escalation Required: {case.escalation_required}
Overall Case Status: {case.overall_case_status}
"""
    raw_response = call_llm(SUMMARY_SYSTEM_PROMPT, user_prompt, json_mode=True, mock_kind="summary")

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        logger.error("Summary generator got non-JSON response for %s: %s", case.source_file, exc)
        raise ValueError(f"LLM did not return valid JSON summary for {case.source_file}") from exc

    data["source_file"] = case.source_file

    try:
        summary = CaseSummary(**data)
    except ValidationError as exc:
        logger.error("Summary schema validation failed for %s: %s", case.source_file, exc)
        raise

    return summary
