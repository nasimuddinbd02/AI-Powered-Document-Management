"""
Document summarization service using LangChain + OpenAI.
"""

import json
import logging
import os

from django.conf import settings

from apps.ai_engine.models import AISummary

logger = logging.getLogger(__name__)


def generate_summary(document):
    """
    Generates a structured AI summary for the given document.

    Uses the document's extracted_text (or description as fallback)
    and produces a summary with key topics and entities.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    llm = ChatOpenAI(
        temperature=0.3,
        model=model,
        openai_api_key=api_key,
        max_tokens=2048,
    )

    # Get document text
    text_content = document.extracted_text or ""
    if not text_content.strip():
        text_content = document.description or "No content available."

    # Truncate to avoid token limits
    if len(text_content) > 12000:
        text_content = text_content[:12000] + "\n\n[Content truncated...]"

    system_prompt = (
        "You are a document analysis AI. Analyze the provided document text and "
        "return a JSON object with the following structure:\n"
        "{\n"
        '  "summary": "A comprehensive 2-3 paragraph summary of the document",\n'
        '  "key_topics": ["topic1", "topic2", ...],\n'
        '  "entities": {\n'
        '    "people": ["name1", "name2"],\n'
        '    "organizations": ["org1", "org2"],\n'
        '    "dates": ["date1", "date2"],\n'
        '    "concepts": ["concept1", "concept2"]\n'
        "  }\n"
        "}\n\n"
        "Return ONLY valid JSON, no other text."
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document Title: {document.title}\n\nDocument Text:\n{text_content}"),
        ])

        # Parse the response
        response_text = response.content.strip()
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

        try:
            parsed = json.loads(response_text)
            summary_text = parsed.get("summary", response_text)
            key_topics = parsed.get("key_topics", [])
            entities = parsed.get("entities", {})
        except json.JSONDecodeError:
            summary_text = response_text
            key_topics = []
            entities = {}

        summary = AISummary.objects.create(
            document=document,
            version_number=document.current_version,
            summary=summary_text,
            key_topics=key_topics,
            entities=entities,
            model_used=model,
        )

        # Update document AI status
        document.ai_status = "completed"
        document.save(update_fields=["ai_status"])

        return summary

    except Exception as e:
        logger.error("Summary generation failed for document %s: %s", document.id, e, exc_info=True)
        document.ai_status = "failed"
        document.save(update_fields=["ai_status"])
        raise
