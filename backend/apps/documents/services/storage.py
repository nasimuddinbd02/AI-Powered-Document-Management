"""
Document storage service.

Provides an abstraction layer over Django's file storage backends,
supporting local filesystem and (optionally) cloud storage.
"""

import logging
import os

from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class DocumentStorageService:
    """
    Manages physical file storage operations.
    """

    def __init__(self):
        self.storage = default_storage

    def store_file(self, file, path):
        """
        Save a file to storage at the given path.

        Args:
            file: Django UploadedFile or similar file-like object.
            path: Destination path relative to MEDIA_ROOT.

        Returns:
            str: The actual stored path (may differ if a name collision was resolved).
        """
        stored_path = self.storage.save(path, file)
        logger.debug("Stored file at: %s", stored_path)
        return stored_path

    def retrieve_file(self, path):
        """
        Open a file from storage.

        Args:
            path: Path relative to MEDIA_ROOT.

        Returns:
            File object or None if not found.
        """
        try:
            if self.storage.exists(path):
                return self.storage.open(path, "rb")
            logger.warning("File not found at path: %s", path)
            return None
        except Exception as e:
            logger.error("Error retrieving file at %s: %s", path, e)
            return None

    def delete_file(self, path):
        """
        Delete a file from storage.

        Args:
            path: Path relative to MEDIA_ROOT.

        Returns:
            bool: True if deleted, False otherwise.
        """
        try:
            if self.storage.exists(path):
                self.storage.delete(path)
                logger.info("Deleted file: %s", path)
                return True
            logger.warning("Cannot delete — file not found: %s", path)
            return False
        except Exception as e:
            logger.error("Error deleting file at %s: %s", path, e)
            return False

    def file_exists(self, path):
        """Check whether a file exists in storage."""
        return self.storage.exists(path)

    def get_file_url(self, path):
        """
        Return a URL for accessing the file.

        For local storage this returns a media-relative URL; for
        cloud storage it returns the full URL.
        """
        try:
            return self.storage.url(path)
        except Exception:
            return None

    def get_file_size(self, path):
        """Return the file size in bytes, or 0 if not found."""
        try:
            return self.storage.size(path)
        except Exception:
            return 0

    def copy_file(self, source_path, dest_path):
        """
        Copy a file from one storage path to another.

        Args:
            source_path: Source path relative to MEDIA_ROOT.
            dest_path: Destination path relative to MEDIA_ROOT.

        Returns:
            str: The actual stored destination path.
        """
        source_file = self.retrieve_file(source_path)
        if source_file is None:
            raise FileNotFoundError(f"Source file not found: {source_path}")
        try:
            stored_path = self.storage.save(dest_path, source_file)
            return stored_path
        finally:
            source_file.close()
