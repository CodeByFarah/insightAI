"""Filesystem storage for uploaded CSV files.

Uploads are written under a generated key, never under the name the client
supplied, so a crafted filename cannot escape the storage directory.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import InvalidFileError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv"}
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",
    "application/octet-stream",
}
UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str) -> str:
    """Reduce a client-supplied name to a safe, display-only basename."""
    base = Path(filename or "").name
    base = UNSAFE_CHARS.sub("_", base).strip("._")
    if not base:
        return "upload.csv"
    return base[:255]


def validate_upload(filename: str, content_type: str | None) -> str:
    """Check extension and declared type, returning the sanitized filename."""
    safe_name = sanitize_filename(filename)
    if Path(safe_name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise InvalidFileError("Only CSV files are accepted. Upload a file ending in .csv.")
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise InvalidFileError(f"Unsupported content type: {content_type}.")
    return safe_name


def build_storage_key(safe_filename: str) -> str:
    return f"{uuid.uuid4().hex}{Path(safe_filename).suffix.lower()}"


def storage_path(storage_key: str) -> Path:
    """Resolve a storage key inside the storage directory, and nowhere else."""
    root = get_settings().storage_dir.resolve()
    candidate = (root / Path(storage_key).name).resolve()
    if candidate.parent != root:
        raise InvalidFileError("Invalid storage location.")
    return candidate


def write_file(storage_key: str, content: bytes) -> Path:
    path = storage_path(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def delete_file(storage_key: str) -> None:
    try:
        storage_path(storage_key).unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not delete stored file %s", storage_key, exc_info=True)
