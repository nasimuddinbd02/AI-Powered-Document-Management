"""
QA chain service using modern LangChain + OpenAI.

Implements RAG (Retrieval-Augmented Generation) over user documents
using extracted text stored in the database.
"""

import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_llm():
    """Create and return an OpenAI chat model instance."""
    from langchain_openai import ChatOpenAI

    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    return ChatOpenAI(
        temperature=0.3,
        model=model,
        openai_api_key=api_key,
        max_tokens=2048,
    )


def _retrieve_context(query, doc_ids, top_k=5):
    """
    Retrieve relevant document context for a query.

    Searches the extracted_text of user documents using simple keyword
    relevance (no embedding required — works immediately on any document).
    Falls back to vector search if embeddings exist.
    """
    from apps.documents.models import Document

    results = []

    # Strategy 1: Direct text search from Document.extracted_text
    documents = Document.objects.filter(id__in=doc_ids).exclude(extracted_text="")
    for doc in documents:
        text = doc.extracted_text or ""
        if not text.strip():
            continue

        # Split text into chunks of ~800 chars for context
        chunks = _chunk_text(text, chunk_size=800, overlap=100)
        query_lower = query.lower()
        query_words = query_lower.split()

        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            # Score by word match count
            score = sum(1 for w in query_words if w in chunk_lower)
            if score > 0:
                results.append({
                    "chunk": chunk,
                    "document_id": doc.id,
                    "document_uuid": str(doc.uuid),
                    "document_title": doc.title,
                    "score": score / len(query_words) if query_words else 0,
                })

    # If no keyword matches, include first chunk of each document for general questions
    if not results:
        for doc in documents:
            text = doc.extracted_text or ""
            if text.strip():
                chunks = _chunk_text(text, chunk_size=800, overlap=100)
                if chunks:
                    results.append({
                        "chunk": chunks[0],
                        "document_id": doc.id,
                        "document_uuid": str(doc.uuid),
                        "document_title": doc.title,
                        "score": 0.3,
                    })

    # Strategy 2: Always include document metadata for all user docs
    all_docs = Document.objects.filter(id__in=doc_ids)
    for doc in all_docs:
        meta_info = (
            f"Document Title: {doc.title}\n"
            f"Original Filename: {doc.original_filename}\n"
            f"File Type: {doc.file_type}\n"
            f"File Size: {doc.file_size} bytes\n"
            f"Uploaded: {doc.created_at}\n"
            f"Last Modified: {doc.updated_at}\n"
        )
        if doc.description:
            meta_info += f"Description: {doc.description}\n"
        if doc.category:
            meta_info += f"Category: {doc.category.name}\n"
        tags = doc.tags.all()
        if tags:
            meta_info += f"Tags: {', '.join(t.name for t in tags)}\n"
        meta_info += f"AI Processed: {doc.ai_status}\n"
        meta_info += f"OCR Status: {doc.ocr_status}\n"

        results.append({
            "chunk": meta_info,
            "document_id": doc.id,
            "document_uuid": str(doc.uuid),
            "document_title": doc.title,
            "score": 0.2,
        })

    # Sort by relevance and return top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _chunk_text(text, chunk_size=800, overlap=100):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def answer_question(question, doc_ids):
    """
    Answer a question using RAG over the user's documents.

    Args:
        question: The user's question.
        doc_ids: List of document IDs the user has access to.

    Returns:
        tuple: (answer_text, source_references)
    """
    context_results = _retrieve_context(question, doc_ids)

    if not context_results:
        # No documents to search — answer from general knowledge with disclaimer
        try:
            llm = _get_llm()
            response = llm.invoke(
                f"The user asked: {question}\n\n"
                "You are an AI document assistant. The user has no documents uploaded yet, "
                "or none contain relevant information. Politely let them know and offer "
                "to help once they upload documents. Keep the response friendly and brief."
            )
            return response.content, []
        except Exception as e:
            logger.error("LLM invocation failed: %s", e)
            return "I couldn't process your request. Please make sure the AI service is configured correctly.", []

    # Build context string
    context_text = "\n\n---\n\n".join(
        f"[Source: {r['document_title']}]\n{r['chunk']}" for r in context_results
    )

    # Build prompt
    system_prompt = (
        "You are an intelligent AI document assistant. Your job is to answer the user's "
        "question based ONLY on the document context provided below. If the answer is not "
        "in the context, say so honestly. Always cite which document you found the information in.\n\n"
        "Format your response using markdown:\n"
        "- Use **bold** for key terms\n"
        "- Use bullet points for lists\n"
        "- Use numbered lists for steps\n"
        "- Keep responses clear and well-structured\n"
    )

    user_prompt = f"Context from documents:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

    try:
        llm = _get_llm()
        from langchain_core.messages import HumanMessage, SystemMessage

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Build source references
        seen_docs = set()
        sources = []
        for r in context_results:
            doc_id = r["document_id"]
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    "document_id": doc_id,
                    "document_uuid": r["document_uuid"],
                    "document_title": r["document_title"],
                    "excerpt": r["chunk"][:200] + "..." if len(r["chunk"]) > 200 else r["chunk"],
                    "relevance_score": round(r["score"], 2),
                })

        return response.content, sources

    except Exception as e:
        logger.error("LLM invocation failed: %s", e, exc_info=True)
        return f"I encountered an error while processing your question: {str(e)}", []


def chat_with_documents(question, doc_ids, chat_history=None):
    """
    Chat with documents using conversation history for multi-turn context.

    Args:
        question: The user's current message.
        doc_ids: List of document IDs the user has access to.
        chat_history: List of dicts with 'role' and 'content' keys.

    Returns:
        tuple: (answer_text, source_references)
    """
    context_results = _retrieve_context(question, doc_ids)

    # Build context
    context_text = "\n\n---\n\n".join(
        f"[Source: {r['document_title']}]\n{r['chunk']}" for r in context_results
    ) if context_results else "No relevant documents found."

    system_prompt = (
        "You are an intelligent AI document assistant for an enterprise document management system. "
        "Help the user by answering questions about their documents using the context provided. "
        "If no document context is relevant, be helpful and suggest what they could do.\n\n"
        "Format your response using markdown:\n"
        "- Use **bold** for key terms and document names\n"
        "- Use bullet points or numbered lists when appropriate\n"
        "- Keep responses clear, structured, and professional\n"
        "- Always mention which document you found information in\n\n"
        f"Document Context:\n{context_text}"
    )

    try:
        llm = _get_llm()
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = [SystemMessage(content=system_prompt)]

        # Add chat history for multi-turn conversation
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context window
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=question))

        response = llm.invoke(messages)

        # Build source references
        seen_docs = set()
        sources = []
        for r in context_results:
            doc_id = r["document_id"]
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    "document_id": doc_id,
                    "document_uuid": r["document_uuid"],
                    "document_title": r["document_title"],
                    "excerpt": r["chunk"][:200] + "..." if len(r["chunk"]) > 200 else r["chunk"],
                    "relevance_score": round(r["score"], 2),
                })

        return response.content, sources

    except Exception as e:
        logger.error("Chat with documents failed: %s", e, exc_info=True)
        return f"I encountered an error: {str(e)}", []
