"""
Common base models for the AI-Powered Document Management System.

Provides reusable abstract models with automatic timestamping.
"""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating ``created_at`` and
    ``updated_at`` fields.

    All project models should inherit from this to get consistent
    timestamp tracking.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(TimeStampedModel):
    """
    Abstract model that uses a UUID as the primary key.

    Useful for models where sequential IDs should not be exposed
    in public-facing APIs.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
