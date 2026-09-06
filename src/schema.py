"""
Pydantic models used across the project.

Using Pydantic here forces the LLM's output into a fixed shape instead of
letting us save whatever raw text the model returns. If the model's JSON
does not match this schema, Pydantic raises a validation error and our
calling code can catch it and retry / log it, instead of writing garbage
to the final report.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ComplaintCase(BaseModel):
    """Structured information extracted from a single complaint document."""

    source_file: str = Field(description="Name of the original document")

    customer_name: str = Field(description="Full name of the customer")
    email: Optional[str] = Field(default=None, description="Customer email address, if present in the document")
    phone_number: Optional[str] = Field(default=None, description="Customer phone number, if present in the document")

    complaint_category: str = Field(
        description="Short category label, e.g. Billing, Product Defect, Delivery, Service Quality, Account Access"
    )
    issue_description: str = Field(description="One or two sentence summary of what went wrong")
    resolution_provided: str = Field(
        description="What resolution, if any, has already been offered or applied. Use 'None provided' if nothing was done yet."
    )

    is_complaint: Literal["Yes", "No"] = Field(description="Whether this document is actually a customer complaint")
    escalation_required: Literal["Yes", "No"] = Field(
        description="Whether this case needs to be escalated to a senior team / manager"
    )
    supporting_document_available: Literal["Yes", "No"] = Field(
        description="Whether the customer mentions attaching proof such as invoices, screenshots, photos, etc."
    )

    overall_case_status: Literal["Open", "In Progress", "Resolved", "Escalated"] = Field(
        description="Current status of the case based on the document content"
    )


class CaseSummary(BaseModel):
    """Internal, management-facing summary generated for a single case."""

    source_file: str
    case_overview: str
    key_issue: str
    action_taken: str
    current_status: str
    recommended_next_action: str
