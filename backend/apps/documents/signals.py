"""
Django signals for the documents app.

Triggers AI processing after a new document is created.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def trigger_document_processing(sender, instance, created, **kwargs):
    """
    After a new document is created, queue AI tasks for
    text extraction, summarisation, and embedding generation.
    """
    if created:
        try:
            from apps.ai_engine.tasks import process_document_task
            process_document_task.delay(instance.id)
            logger.info("Queued AI processing for document %s", instance.uuid)
        except Exception as e:
            # Don't fail the request if Celery is unavailable
            logger.warning(
                "Could not queue AI processing for document %s: %s",
                instance.uuid,
                e,
            )
