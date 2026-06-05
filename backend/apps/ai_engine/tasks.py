"""
Celery tasks for the AI engine.

These tasks run asynchronously to avoid blocking the API.
When Celery is not available, the views fall back to synchronous execution.
"""

import logging

logger = logging.getLogger(__name__)


def _get_document(document_id):
    """Helper to fetch a document by ID."""
    from apps.documents.models import Document
    return Document.objects.get(id=document_id)


try:
    from celery import shared_task

    @shared_task
    def generate_summary_task(document_id):
        """Generate an AI summary for a document (Celery task)."""
        try:
            from .services.summarizer import generate_summary
            document = _get_document(document_id)
            generate_summary(document)
            return f"Summary generated for document {document_id}"
        except Exception as e:
            logger.error("Error generating summary for %s: %s", document_id, e)
            raise

    @shared_task
    def process_embeddings_task(document_id):
        """Process document embeddings for semantic search (Celery task)."""
        try:
            from .services.embeddings import process_document_embeddings
            document = _get_document(document_id)
            process_document_embeddings(document)
            return f"Embeddings processed for document {document_id}"
        except Exception as e:
            logger.error("Error processing embeddings for %s: %s", document_id, e)
            raise

    @shared_task
    def process_document_task(document_id):
        """Orchestrate all AI processing for a document (Celery task)."""
        try:
            document = _get_document(document_id)
            
            # 1. Generate summary
            try:
                from .services.summarizer import generate_summary
                generate_summary(document)
                logger.info("Summary generated successfully for document %s", document_id)
            except Exception as e:
                logger.error("Failed to generate summary for document %s: %s", document_id, e)

            # 2. Process embeddings
            try:
                from .services.embeddings import process_document_embeddings
                process_document_embeddings(document)
                logger.info("Embeddings processed successfully for document %s", document_id)
            except Exception as e:
                logger.error("Failed to process embeddings for document %s: %s", document_id, e)

            return f"AI processing complete for document {document_id}"
        except Exception as e:
            logger.error("Error in process_document_task for %s: %s", document_id, e)
            raise

except ImportError:
    # Celery not installed — provide dummy task functions
    logger.warning("Celery not available. AI tasks will not run asynchronously.")

    def generate_summary_task(document_id):
        from .services.summarizer import generate_summary
        document = _get_document(document_id)
        return generate_summary(document)

    def process_embeddings_task(document_id):
        from .services.embeddings import process_document_embeddings
        document = _get_document(document_id)
        return process_document_embeddings(document)

    def process_document_task(document_id):
        from .services.summarizer import generate_summary
        from .services.embeddings import process_document_embeddings
        document = _get_document(document_id)
        
        try:
            generate_summary(document)
        except Exception as e:
            logger.error("Sync summary failed: %s", e)
            
        try:
            process_document_embeddings(document)
        except Exception as e:
            logger.error("Sync embeddings failed: %s", e)
            
        return f"Synchronous AI processing complete for document {document_id}"
