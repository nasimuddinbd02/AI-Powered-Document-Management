"""
Document upload service.

Handles file validation, storage, initial version creation,
and metadata extraction during document upload.
"""

import logging
import os

from django.db import transaction

from apps.common.utils import (
    calculate_file_checksum,
    get_file_extension,
    get_mime_type,
)
from apps.documents.models import (
    Document,
    DocumentMetadata,
    DocumentTag,
    DocumentVersion,
)

logger = logging.getLogger(__name__)


class DocumentUploadService:
    """
    Orchestrates the document upload workflow:
    1. Create the Document record.
    2. Create the initial DocumentVersion.
    3. Attach tags and metadata.
    4. Extract basic file metadata.
    """

    @transaction.atomic
    def create_document(
        self,
        file,
        title,
        description,
        owner,
        category=None,
        tag_ids=None,
        metadata_items=None,
    ):
        """
        Create a new document from an uploaded file.

        Args:
            file: The uploaded file object.
            title: Document title.
            description: Document description.
            owner: User who owns the document.
            category: Optional Category instance.
            tag_ids: Optional list of Tag IDs to attach.
            metadata_items: Optional list of metadata dicts.

        Returns:
            Document: The newly created document.
        """
        tag_ids = tag_ids or []
        metadata_items = metadata_items or []

        ext = get_file_extension(file.name)
        file_type = self._resolve_file_type(ext)

        # Create the document
        document = Document.objects.create(
            title=title,
            description=description,
            file=file,
            file_type=file_type,
            file_size=file.size,
            original_filename=file.name,
            storage_path=file.name,  # Will be set by upload_to
            owner=owner,
            category=category,
            current_version=1,
            ocr_status=self._determine_ocr_status(file_type),
        )

        # Update storage_path to the actual path after save
        document.storage_path = document.file.name
        document.save(update_fields=["storage_path"])

        # Create the initial version
        checksum = calculate_file_checksum(file)
        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=document.file,
            file_path=document.file.name,
            file_size=file.size,
            change_note="Initial upload",
            checksum=checksum,
            uploaded_by=owner,
        )

        # Attach tags
        for tag_id in tag_ids:
            try:
                DocumentTag.objects.create(document=document, tag_id=tag_id)
            except Exception as e:
                logger.warning("Could not attach tag %s to document %s: %s", tag_id, document.uuid, e)

        # Add metadata
        for item in metadata_items:
            try:
                DocumentMetadata.objects.create(
                    document=document,
                    key=item.get("key", ""),
                    value=item.get("value", ""),
                    value_type=item.get("value_type", "string"),
                )
            except Exception as e:
                logger.warning("Could not add metadata to document %s: %s", document.uuid, e)

        # Auto-extract file metadata
        self._extract_file_metadata(document, file)

        # Auto-extract text content for AI processing
        self._extract_text_content(document, file)

        logger.info("Document '%s' created successfully (UUID: %s)", title, document.uuid)
        return document

    def _resolve_file_type(self, ext):
        """Map file extension to Document.FileType."""
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
        return type_map.get(ext, Document.FileType.OTHER)

    def _determine_ocr_status(self, file_type):
        """Determine the initial OCR status based on file type."""
        image_types = {Document.FileType.PNG, Document.FileType.JPG, Document.FileType.JPEG}
        if file_type in image_types:
            return Document.OCRStatus.PENDING
        return Document.OCRStatus.NOT_APPLICABLE

    def _extract_file_metadata(self, document, file):
        """
        Extract and store basic metadata from the file.
        """
        metadata_entries = [
            ("mime_type", get_mime_type(file.name), "string"),
            ("extension", get_file_extension(file.name), "string"),
        ]

        for key, value, vtype in metadata_entries:
            DocumentMetadata.objects.update_or_create(
                document=document,
                key=key,
                defaults={"value": value, "value_type": vtype},
            )

    def _extract_text_content(self, document, file):
        """
        Extract text content from the uploaded file for AI processing.

        Supports PDF (via PyPDF2) and plain text files.
        """
        try:
            file.seek(0)  # Reset file pointer
            text = ""

            if document.file_type == Document.FileType.PDF:
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(file)
                    pages = []
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            pages.append(page_text)
                    text = "\n\n".join(pages)

                    # Store page count as metadata
                    DocumentMetadata.objects.update_or_create(
                        document=document,
                        key="page_count",
                        defaults={"value": str(len(reader.pages)), "value_type": "integer"},
                    )
                except ImportError:
                    logger.warning("PyPDF2 not installed — cannot extract PDF text.")
                except Exception as e:
                    logger.warning("PDF text extraction failed for %s: %s", document.uuid, e)

            elif document.file_type == Document.FileType.TXT:
                try:
                    text = file.read().decode("utf-8", errors="ignore")
                except Exception:
                    text = file.read().decode("latin-1", errors="ignore")

            elif document.file_type == Document.FileType.CSV:
                try:
                    text = file.read().decode("utf-8", errors="ignore")
                except Exception:
                    text = file.read().decode("latin-1", errors="ignore")

            elif document.file_type in (Document.FileType.DOC, Document.FileType.DOCX):
                try:
                    import docx
                    doc = docx.Document(file)
                    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                except ImportError:
                    logger.warning("python-docx not installed — cannot extract DOCX text.")
                except Exception as e:
                    logger.warning("DOCX text extraction failed for %s: %s", document.uuid, e)

            if text.strip():
                document.extracted_text = text.strip()
                document.save(update_fields=["extracted_text"])
                logger.info(
                    "Extracted %d chars of text from document %s",
                    len(document.extracted_text), document.uuid,
                )

                # Store word count as metadata
                word_count = len(text.split())
                DocumentMetadata.objects.update_or_create(
                    document=document,
                    key="word_count",
                    defaults={"value": str(word_count), "value_type": "integer"},
                )

        except Exception as e:
            logger.error("Text extraction failed for document %s: %s", document.uuid, e)
