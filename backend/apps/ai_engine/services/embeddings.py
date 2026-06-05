import logging
from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def process_document_embeddings(document):
    """
    Generate OpenAI vector embeddings for the document's extracted text,
    store them in the database, and index them in the FAISS vector store.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise Exception("OpenAI API Key not configured")

    embeddings_model = OpenAIEmbeddings(
        openai_api_key=api_key,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    text = document.extracted_text
    if not text or not text.strip():
        logger.warning("No extracted text found for document %s (ID: %s)", document.title, document.id)
        return

    chunks = text_splitter.split_text(text)
    if not chunks:
        logger.warning("Text splitting yielded 0 chunks for document %s", document.title)
        return

    logger.info("Generating embeddings for %d chunks of document '%s'", len(chunks), document.title)
    
    # Generate embeddings
    embeddings = embeddings_model.embed_documents(chunks)
    
    # Store and update FAISS index
    from apps.search.services.semantic import SemanticSearchService
    semantic_service = SemanticSearchService()
    semantic_service.index_document(document.id, chunks, embeddings)
    
    # Update AI status
    document.ai_status = "completed"
    document.save(update_fields=["ai_status"])
    logger.info("Successfully updated FAISS and DB embeddings for document '%s'", document.title)
