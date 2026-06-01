"""
Document versioning service.

Handles creating new versions of existing documents, restoring
previous versions, and comparing versions.
"""

import logging

from django.db import transaction

from apps.common.utils import calculate_file_checksum, get_file_extension
from apps.documents.models import Document, DocumentVersion

logger = logging.getLogger(__name__)


class DocumentVersioningService:
    """
    Manages document version lifecycle:
    - Upload a new version
    - Restore a previous version
    - List version history
    """

    @transaction.atomic
    def create_new_version(self, document, file, change_note="", uploaded_by=None):
        """
        Upload a new version of an existing document.

        Args:
            document: The Document instance to version.
            file: The new file to store.
            change_note: Description of changes.
            uploaded_by: User performing the upload.

        Returns:
            DocumentVersion: The newly created version.
        """
        new_version_number = document.current_version + 1
        checksum = calculate_file_checksum(file)

        # Check for duplicate content
        latest_version = document.versions.order_by("-version_number").first()
        if latest_version and latest_version.checksum == checksum:
            logger.info(
                "Skipping version creation — file is identical to v%d",
                latest_version.version_number,
            )
            raise ValueError("The uploaded file is identical to the current version.")

        version = DocumentVersion.objects.create(
            document=document,
            version_number=new_version_number,
            file=file,
            file_path=file.name,
            file_size=file.size,
            change_note=change_note,
            checksum=checksum,
            uploaded_by=uploaded_by,
        )

        # Update the document's current version and file reference
        document.current_version = new_version_number
        document.file = version.file
        document.file_size = file.size
        document.storage_path = version.file.name

        ext = get_file_extension(file.name)
        type_map = {
            "pdf": Document.FileType.PDF,
            "doc": Document.FileType.DOC,
            "docx": Document.FileType.DOCX,
            "txt": Document.FileType.TXT,
            "png": Document.FileType.PNG,
            "jpg": Document.FileType.JPG,
            "jpeg": Document.FileType.JPEG,
            "xlsx": Document.FileType.XLSX,
            "csv": Document.FileType.CSV,
        }
        document.file_type = type_map.get(ext, Document.FileType.OTHER)
        document.save()

        logger.info(
            "Created version %d for document %s",
            new_version_number,
            document.uuid,
        )
        return version

    @transaction.atomic
    def restore_version(self, document, version_number, restored_by=None):
        """
        Restore a document to a previous version by creating a new
        version that copies the old version's file.

        Args:
            document: The Document instance.
            version_number: The version number to restore.
            restored_by: User performing the restore.

        Returns:
            DocumentVersion: The newly created version.
        """
        try:
            old_version = document.versions.get(version_number=version_number)
        except DocumentVersion.DoesNotExist:
            raise ValueError(f"Version {version_number} does not exist.")

        new_version_number = document.current_version + 1

        version = DocumentVersion.objects.create(
            document=document,
            version_number=new_version_number,
            file=old_version.file,
            file_path=old_version.file_path,
            file_size=old_version.file_size,
            change_note=f"Restored from version {version_number}",
            checksum=old_version.checksum,
            uploaded_by=restored_by,
        )

        document.current_version = new_version_number
        document.file = old_version.file
        document.file_size = old_version.file_size
        document.storage_path = old_version.file_path
        document.save()

        logger.info(
            "Restored document %s to version %d (now v%d)",
            document.uuid,
            version_number,
            new_version_number,
        )
        return version

    def get_version_history(self, document):
        """Return all versions for a document, ordered by version number."""
        return document.versions.select_related("uploaded_by").order_by("-version_number")

    def get_version(self, document, version_number):
        """Retrieve a specific version of a document."""
        try:
            return document.versions.get(version_number=version_number)
        except DocumentVersion.DoesNotExist:
            return None
