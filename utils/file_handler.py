"""
File handler: reads PDF, DOCX, and TXT resume files into plain text.
"""
import os
import tempfile
from pathlib import Path
from typing import Tuple

from utils.security import sanitize_text, validate_file


def read_pdf(file_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return sanitize_text("\n".join(pages))


def read_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return sanitize_text("\n".join(paragraphs))


def read_txt(file_path: str) -> str:
    """Read a plain-text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return sanitize_text(f.read())


def read_resume_file(file_path: str) -> Tuple[str, str]:
    """
    Read a resume from disk.
    Returns (text_content, filename).
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_path), path.name
    elif ext in (".docx", ".doc"):
        return read_docx(file_path), path.name
    elif ext == ".txt":
        return read_txt(file_path), path.name
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: PDF, DOCX, TXT")


def read_uploaded_file(uploaded_file) -> Tuple[str, str]:
    """
    Read a Streamlit UploadedFile object.
    Validates, writes to a temp file, reads, then cleans up.
    Returns (text_content, filename).
    """
    ok, err = validate_file(uploaded_file.name, len(uploaded_file.getvalue()))
    if not ok:
        raise ValueError(err)

    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        content, _ = read_resume_file(tmp_path)
        return content, uploaded_file.name
    finally:
        os.unlink(tmp_path)
