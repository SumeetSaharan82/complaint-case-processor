"""
Document ingestion.

Responsible for finding files in the data/ folder and turning each one
into plain text, regardless of whether it started life as a .txt, .pdf
or .docx file. Kept separate from the LLM logic so that adding a new
file format later only means touching this one file.
"""

import logging
from pathlib import Path
from typing import Optional

from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def read_txt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n".join(pages_text)


def read_docx(file_path: Path) -> str:
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def load_document_text(file_path: Path) -> Optional[str]:
    """
    Read a single document and return its text content.

    Returns None (instead of raising) if the file cannot be read, so the
    batch runner can skip it and move on to the next document rather than
    crashing the whole run.
    """
    extension = file_path.suffix.lower()

    try:
        if extension == ".txt":
            text = read_txt(file_path)
        elif extension == ".pdf":
            text = read_pdf(file_path)
        elif extension == ".docx":
            text = read_docx(file_path)
        else:
            logger.warning("Skipping unsupported file type: %s", file_path.name)
            return None

        text = text.strip()
        if not text:
            logger.warning("No extractable text found in: %s", file_path.name)
            return None

        return text

    except Exception as exc:
        # Broad except is intentional here: a single corrupt/locked file
        # should not stop the entire batch from processing.
        logger.error("Failed to read %s: %s", file_path.name, exc)
        return None


def load_documents_from_folder(folder_path: str) -> dict:
    """
    Scan `folder_path` for supported files and return a dict mapping
    file name -> extracted text, for every file that was read successfully.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Data folder not found: {folder_path}")

    documents = {}
    all_files = sorted(folder.iterdir())

    for file_path in all_files:
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = load_document_text(file_path)
        if text is not None:
            documents[file_path.name] = text
            logger.info("Loaded document: %s (%d characters)", file_path.name, len(text))

    return documents
