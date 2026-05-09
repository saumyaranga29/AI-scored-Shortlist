"""
Security utilities: input sanitisation, PII masking, file validation.
These mitigations are mandatory per the project brief.
"""
import re
from pathlib import Path

# ── Prompt-injection patterns ────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore (?:previous|all|above|prior) (?:instructions?|prompts?|context)",
    r"(?:system|assistant)\s*:\s*",
    r"you are now",
    r"new (?:role|persona|instruction)",
    r"forget (?:everything|all|previous)",
    r"override (?:your|all)",
    r"act as (?:a |an )?(?:different|new)",
    r"disregard (?:your|all)",
    r"</?(?:system|user|assistant|prompt|instruction)>",
    r"jailbreak",
    r"DAN mode",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE_MB = 10


def sanitize_text(text: str, max_length: int = 60_000) -> str:
    """
    Sanitize resume / JD text:
    - Truncate to max_length characters
    - Neutralize prompt-injection patterns
    """
    if not text:
        return ""
    text = text[:max_length]
    for pattern in _COMPILED:
        text = pattern.sub(
            lambda m: f"[FILTERED]",
            text,
        )
    return text.strip()


def mask_pii_for_log(text: str) -> str:
    """Mask PII fields so logs never contain plaintext personal data."""
    # Emails
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL_MASKED]",
        text,
    )
    # Phone numbers (international + Indian formats)
    text = re.sub(
        r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b",
        "[PHONE_MASKED]",
        text,
    )
    # Aadhaar-style 12-digit numbers
    text = re.sub(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[ID_MASKED]", text)
    return text


def validate_file(filename: str, size_bytes: int) -> tuple[bool, str]:
    """
    Validate uploaded file.
    Returns (is_valid, error_message).
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        return False, f"File too large ({size_bytes / 1e6:.1f} MB). Max: {MAX_FILE_SIZE_MB} MB"
    return True, ""
