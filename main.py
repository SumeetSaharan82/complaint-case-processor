"""
Entry point for the AI Customer Complaint & Case Processing System.

Usage:
    python main.py

Reads every supported document from the data/ folder, runs the 3-step
GenAI workflow (extraction -> customer email -> internal summary) on
each one, and writes results into the output/ folder plus a consolidated
output/final_report.csv.

See README.md for full setup instructions.
"""

import logging
import sys

from src.workflow import run_batch


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("pipeline.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Customer Complaint & Case Processing System")

    try:
        run_batch()
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.info("Done. Check the output/ folder and pipeline.log for details.")


if __name__ == "__main__":
    main()
