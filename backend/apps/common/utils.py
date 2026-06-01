"""
General-purpose utilities for the Document Management System.
"""

import hashlib
import mimetypes
import os
import uuid
from datetime import datetime

from django.conf import settings
from django.utils.text import slugify


def generate_upload_path(instance, filename):
    """
    Generate a unique upload path for a file.

    Organises files by date and uses UUID filenames to prevent
    collisions and avoid leaking original filenames on disk.

    Returns:
        str: Path like ``documents/2024/01/15/<uuid>.<ext>``
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    now = datetime.now()
    return os.path.join(
        "documents",
        str(now.year),
        str(now.month).zfill(2),
        str(now.day).zfill(2),
        unique_name,
    )


def generate_version_path(document_id, version_number, filename):
    """
    Generate a storage path for a document version.

    Returns:
        str: Path like ``versions/<doc_uuid>/v<n>/<uuid>.<ext>``
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(
        "versions",
        str(document_id),
        f"v{version_number}",
        unique_name,
    )


def calculate_file_checksum(file_obj, algorithm="sha256"):
    """
    Calculate the checksum of a file object.

    Args:
        file_obj: A file-like object (must support read()).
        algorithm: Hash algorithm name (default: sha256).

    Returns:
        str: Hex-encoded checksum string.
    """
    hasher = hashlib.new(algorithm)
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(8192), b""):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def get_file_extension(filename):
    """Extract the file extension from a filename (without the dot)."""
    return os.path.splitext(filename)[1].lower().lstrip(".")


def get_mime_type(filename):
    """
    Determine the MIME type of a file based on its name.

    Returns:
        str: MIME type string, e.g. ``application/pdf``.
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def validate_file_size(file_obj):
    """
    Check that a file does not exceed the configured maximum upload size.

    Raises:
        ValueError: If the file exceeds ``MAX_UPLOAD_SIZE``.
    """
    max_size = getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)
    if file_obj.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValueError(f"File size exceeds the maximum allowed size of {max_mb:.0f} MB.")


def validate_file_type(filename):
    """
    Check that a file's extension is in the list of allowed types.

    Raises:
        ValueError: If the file type is not allowed.
    """
    ext = get_file_extension(filename)
    allowed = getattr(settings, "ALLOWED_FILE_TYPES", {})
    if ext not in allowed:
        raise ValueError(
            f"File type '.{ext}' is not supported. "
            f"Allowed types: {', '.join(allowed.keys())}"
        )


def sanitize_filename(filename):
    """
    Sanitize a filename for safe storage.

    Preserves the extension but slugifies the name portion.
    """
    name, ext = os.path.splitext(filename)
    return f"{slugify(name)}{ext.lower()}"


def format_file_size(size_bytes):
    """
    Format a file size in bytes into a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        str: Formatted size, e.g. ``2.5 MB``.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
