"""
Builds the consolidated final_report.csv from all processed cases.
"""

import logging
from pathlib import Path

import pandas as pd

from src.schema import CaseSummary, ComplaintCase

logger = logging.getLogger(__name__)


def build_final_report(cases: list[ComplaintCase], summaries: dict[str, CaseSummary], output_folder: str) -> str:
    """
    Combine extracted case data with recommended next actions into one
    CSV file, so a manager can open a single spreadsheet instead of
    reading every individual file.
    """
    rows = []
    for case in cases:
        summary = summaries.get(case.source_file)
        rows.append(
            {
                "source_file": case.source_file,
                "customer_name": case.customer_name,
                "email": case.email,
                "phone_number": case.phone_number,
                "complaint_category": case.complaint_category,
                "is_complaint": case.is_complaint,
                "escalation_required": case.escalation_required,
                "supporting_document_available": case.supporting_document_available,
                "overall_case_status": case.overall_case_status,
                "recommended_next_action": summary.recommended_next_action if summary else "",
            }
        )

    df = pd.DataFrame(rows)
    output_path = Path(output_folder) / "final_report.csv"
    df.to_csv(output_path, index=False)
    logger.info("Final report written to %s (%d rows)", output_path, len(df))
    return str(output_path)
