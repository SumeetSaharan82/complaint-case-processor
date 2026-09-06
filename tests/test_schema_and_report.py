"""
Small offline unit tests that don't need an API key.

Run with:
    python -m pytest tests/ -v
or just:
    python -m tests.test_schema_and_report
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schema import ComplaintCase, CaseSummary
from src.report import build_final_report


def test_complaint_case_valid():
    case = ComplaintCase(
        source_file="test.txt",
        customer_name="Test User",
        email="test@example.com",
        phone_number="1234567890",
        complaint_category="Billing",
        issue_description="Overcharged on invoice.",
        resolution_provided="None provided",
        is_complaint="Yes",
        escalation_required="No",
        supporting_document_available="No",
        overall_case_status="Open",
    )
    assert case.customer_name == "Test User"
    assert case.is_complaint == "Yes"


def test_complaint_case_rejects_bad_status():
    try:
        ComplaintCase(
            source_file="test.txt",
            customer_name="Test User",
            complaint_category="Billing",
            issue_description="Overcharged on invoice.",
            resolution_provided="None provided",
            is_complaint="Yes",
            escalation_required="No",
            supporting_document_available="No",
            overall_case_status="Not A Real Status",  # invalid on purpose
        )
        raise AssertionError("Expected a validation error for an invalid status value")
    except Exception as exc:
        assert "overall_case_status" in str(exc)


def test_build_final_report(tmp_path):
    case = ComplaintCase(
        source_file="test.txt",
        customer_name="Test User",
        complaint_category="Billing",
        issue_description="Overcharged on invoice.",
        resolution_provided="None provided",
        is_complaint="Yes",
        escalation_required="No",
        supporting_document_available="No",
        overall_case_status="Open",
    )
    summary = CaseSummary(
        source_file="test.txt",
        case_overview="Customer was overcharged.",
        key_issue="Billing error.",
        action_taken="None yet",
        current_status="Open",
        recommended_next_action="Refund the customer.",
    )
    output_path = build_final_report([case], {"test.txt": summary}, str(tmp_path))
    assert Path(output_path).exists()
    content = Path(output_path).read_text()
    assert "Test User" in content
    assert "Refund the customer." in content


if __name__ == "__main__":
    test_complaint_case_valid()
    test_complaint_case_rejects_bad_status()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_build_final_report(Path(tmp))
    print("All tests passed.")
