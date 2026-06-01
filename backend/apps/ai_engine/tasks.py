from celery import shared_task
import logging
from apps.documents.models import Document
from .services.summarizer import generate_summary
from .services.embeddings import process_document_embeddings

logger = logging.getLogger(__name__)

@shared_task
def generate_summary_task(document_id):
    try:
        document = Document.objects.get(id=document_id)
        generate_summary(document)
        return f"Summary generated for document {document_id}"
    except Exception as e:
        logger.error(f"Error generating summary for {document_id}: {str(e)}")
        raise

@shared_task
def process_embeddings_task(document_id):
    try:
        document = Document.objects.get(id=document_id)
        process_document_embeddings(document)
        return f"Embeddings processed for document {document_id}"
    except Exception as e:
        logger.error(f"Error processing embeddings for {document_id}: {str(e)}")
        raise
