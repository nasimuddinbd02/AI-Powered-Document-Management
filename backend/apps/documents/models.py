"""
Document models for the AI-Powered Document Management System.

Defines Document, DocumentVersion, DocumentMetadata, Tag, Category,
DocumentAccess, and M2M through tables.
"""

import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.utils import generate_upload_path


class Category(TimeStampedModel):
    """
    Hierarchical category for organising documents.

    Supports self-referencing parent for nested categories.
    """

    name = models.CharField(
        max_length=100,
        help_text="Category name.",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="URL-friendly slug for the category.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this category.",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent category for hierarchy.",
    )

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def full_path(self):
        """Return the full category path, e.g. 'Engineering > Backend > API'."""
        parts = [self.name]
        current = self.parent
        while current:
            parts.insert(0, current.name)
            current = current.parent
        return " > ".join(parts)


class Tag(TimeStampedModel):
    """
    Tag that can be attached to documents for flexible classification.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag label.",
    )
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Hex colour code for UI display, e.g. '#3B82F6'.",
    )

    class Meta:
        db_table = "tags"
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(TimeStampedModel):
    """
    Core document model.

    Uses UUID as the public identifier to avoid exposing sequential IDs.
    Tracks file metadata, ownership, and processing status.
    """

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        DOC = "doc", "Word (doc)"
        DOCX = "docx", "Word (docx)"
        TXT = "txt", "Plain Text"
        PNG = "png", "PNG Image"
        JPG = "jpg", "JPEG Image"
        JPEG = "jpeg", "JPEG Image"
        XLSX = "xlsx", "Excel"
        CSV = "csv", "CSV"
        OTHER = "other", "Other"

    class OCRStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        NOT_APPLICABLE = "n/a", "Not Applicable"

    class AIStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Public UUID for API access.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Document title.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional document description.",
    )
    file = models.FileField(
        upload_to=generate_upload_path,
        help_text="The uploaded document file.",
    )
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
        default=FileType.OTHER,
        help_text="Type of the uploaded file.",
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="File size in bytes.",
    )
    storage_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Physical storage path of the current file.",
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Original filename as uploaded by the user.",
    )
    current_version = models.PositiveIntegerField(
        default=1,
        help_text="Current version number.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="User who owns this document.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Category this document belongs to.",
    )
    tags = models.ManyToManyField(
        Tag,
        through="DocumentTag",
        blank=True,
        related_name="documents",
        help_text="Tags associated with this document.",
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Whether the document is archived.",
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft-delete flag.",
    )
    ocr_status = models.CharField(
        max_length=20,
        choices=OCRStatus.choices,
        default=OCRStatus.PENDING,
        help_text="Status of OCR processing.",
    )
    ai_status = models.CharField(
        max_length=20,
        choices=AIStatus.choices,
        default=AIStatus.PENDING,
        help_text="Status of AI processing (summarisation, embeddings).",
    )
    extracted_text = models.TextField(
        blank=True,
        default="",
        help_text="Full text extracted from the document (via OCR or parsing).",
    )

    class Meta:
        db_table = "documents"
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["file_type"]),
            models.Index(fields=["is_archived", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.title} (v{self.current_version})"

    @property
    def is_image(self):
        return self.file_type in (self.FileType.PNG, self.FileType.JPG, self.FileType.JPEG)

    @property
    def needs_ocr(self):
        return self.is_image and self.ocr_status == self.OCRStatus.PENDING


class DocumentVersion(TimeStampedModel):
    """
    Tracks individual versions of a document.

    Every upload or edit creates a new version so that previous
    versions are preserved and can be restored.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="The document this version belongs to.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Sequential version number.",
    )
    file = models.FileField(
        upload_to="versions/",
        help_text="File for this specific version.",
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Storage path for this version's file.",
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="File size in bytes.",
    )
    change_note = models.TextField(
        blank=True,
        default="",
        help_text="Description of changes in this version.",
    )
    checksum = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="SHA-256 checksum of the file.",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_versions",
        help_text="User who uploaded this version.",
    )

    class Meta:
        db_table = "document_versions"
        verbose_name = "Document Version"
        verbose_name_plural = "Document Versions"
        ordering = ["-version_number"]
        unique_together = ("document", "version_number")

    def __str__(self):
        return f"{self.document.title} — v{self.version_number}"


class DocumentMetadata(TimeStampedModel):
    """
    Flexible key-value metadata associated with a document.
    """

    class ValueType(models.TextChoices):
        STRING = "string", "String"
        INTEGER = "integer", "Integer"
        FLOAT = "float", "Float"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        JSON = "json", "JSON"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="metadata",
        help_text="Document this metadata belongs to.",
    )
    key = models.CharField(
        max_length=100,
        help_text="Metadata key, e.g. 'author', 'page_count'.",
    )
    value = models.TextField(
        help_text="Metadata value (stored as text, interpret via value_type).",
    )
    value_type = models.CharField(
        max_length=10,
        choices=ValueType.choices,
        default=ValueType.STRING,
        help_text="Data type hint for the value.",
    )

    class Meta:
        db_table = "document_metadata"
        verbose_name = "Document Metadata"
        verbose_name_plural = "Document Metadata"
        unique_together = ("document", "key")

    def __str__(self):
        return f"{self.document.title} — {self.key}: {self.value}"


class DocumentTag(TimeStampedModel):
    """
    Through table linking Documents to Tags.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="document_tags",
        help_text="The document.",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="document_tags",
        help_text="The tag.",
    )

    class Meta:
        db_table = "document_tags"
        verbose_name = "Document Tag"
        verbose_name_plural = "Document Tags"
        unique_together = ("document", "tag")

    def __str__(self):
        return f"{self.document.title} — {self.tag.name}"


class DocumentAccess(TimeStampedModel):
    """
    Controls per-user access levels for individual documents.
    """

    class AccessLevel(models.TextChoices):
        VIEWER = "viewer", "Viewer"
        EDITOR = "editor", "Editor"
        ADMIN = "admin", "Admin"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="access_records",
        help_text="The document being shared.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_access",
        help_text="The user who has access.",
    )
    access_level = models.CharField(
        max_length=10,
        choices=AccessLevel.choices,
        default=AccessLevel.VIEWER,
        help_text="Level of access granted.",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_access",
        help_text="User who granted this access.",
    )

    class Meta:
        db_table = "document_access"
        verbose_name = "Document Access"
        verbose_name_plural = "Document Access"
        unique_together = ("document", "user")

    def __str__(self):
        return f"{self.user.email} — {self.access_level} — {self.document.title}"
