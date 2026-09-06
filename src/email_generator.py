"""
Step 2 of the workflow: Extracted Data -> Customer Response Email.

Takes the validated ComplaintCase and writes a short, professional email
back to the customer. This step is intentionally kept separate from
extraction so each LLM call has one clear job (single responsibility),
which also makes it easy to swap out or re-prompt independently.
"""

from src.llm_client import call_llm
from src.schema import ComplaintCase

EMAIL_SYSTEM_PROMPT = """You are a customer support agent writing a short, professional email \
reply to a customer about their complaint.

Rules:
- Address the customer by name.
- Briefly summarize the issue in your own words.
- Mention the resolution or current status honestly, based only on the \
information given to you.
- Do not invent any new facts, dates, refunds, or promises that are not \
in the provided data.
- Keep a polite, professional and empathetic tone.
- Keep the email under 150 words.
- Sign off as "Customer Support Team".
"""


def generate_customer_email(case: ComplaintCase) -> str:
    """Generate a customer-facing response email for one processed case."""
    user_prompt = f"""Write a customer response email using this case information:

Customer Name: {case.customer_name}
Complaint Category: {case.complaint_category}
Issue Description: {case.issue_description}
Resolution Provided: {case.resolution_provided}
Escalation Required: {case.escalation_required}
Current Case Status: {case.overall_case_status}
"""
    email_text = call_llm(EMAIL_SYSTEM_PROMPT, user_prompt, json_mode=False)
    return email_text.strip()
