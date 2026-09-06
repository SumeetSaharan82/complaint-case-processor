"""
Centralised configuration.

Everything that could change between environments (API key, model name,
folder paths) is read from environment variables here, instead of being
hard-coded inside the modules that use them.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads a local .env file, if one exists

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# When true, no real API calls are made. A rule-based fake response is
# returned instead, so the rest of the pipeline (folders, CSV report,
# error handling) can be tested for free / offline.
MOCK_LLM = os.getenv("MOCK_LLM", "false").lower() == "true"

DATA_FOLDER = os.getenv("DATA_FOLDER", "data")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
