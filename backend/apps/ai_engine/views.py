"""
Views for the AI engine app.

Provides document summarization, Q&A, and chat endpoints.
"""

import logging
import uuid as uuid_lib

from rest_framework import status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.documents.models import Document

from .models import AISummary
from .serializers import AISummarySerializer, AskQuestionSerializer, ChatRequestSerializer

logger = logging.getLogger(__name__)


class AISummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for AI summaries."""

    queryset = AISummary.objects.all()
    serializer_class = AISummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(document__owner=self.request.user)


class SummarizeDocumentView(views.APIView):
    """Trigger AI summarization for a document."""

    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        try:
            document = Document.objects.get(uuid=uuid, owner=request.user)
            try:
                from .tasks import generate_summary_task
                task = generate_summary_task.delay(document.id)
                return Response(
                    {"status": "processing", "task_id": task.id},
                    status=status.HTTP_202_ACCEPTED,
                )
            except Exception:
                # Celery not available — run synchronously
                from .services.summarizer import generate_summary
                summary = generate_summary(document)
                return Response(
                    {"status": "completed", "summary": summary.summary},
                    status=status.HTTP_200_OK,
                )
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AskQuestionView(views.APIView):
    """Answer a one-shot question about user documents."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AskQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data["question"]
            doc_uuids = serializer.validated_data.get("document_ids", [])

            docs = Document.objects.filter(owner=request.user)
            if doc_uuids:
                docs = docs.filter(uuid__in=doc_uuids)

            doc_ids = list(docs.values_list("id", flat=True))

            from .services.qa_chain import answer_question
            answer, sources = answer_question(question, doc_ids)
            return Response(
                {"answer": answer, "sources": sources},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatView(views.APIView):
    """
    Multi-turn conversational chat about user documents.

    Accepts the frontend format: { message, conversationId? }
    as well as the legacy format: { question, document_ids?, chat_history? }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        # Support the frontend format { message, conversationId }
        question = data.get("message") or data.get("question", "")
        if not question or not question.strip():
            return Response(
                {"error": "A message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation_id = data.get("conversationId") or data.get("conversation_id")
        if not conversation_id:
            conversation_id = str(uuid_lib.uuid4())

        chat_history = data.get("chat_history", [])
        doc_uuids = data.get("document_ids", [])

        # Fetch all user documents (or filter by UUIDs if provided)
        docs = Document.objects.filter(owner=request.user)
        if doc_uuids:
            docs = docs.filter(uuid__in=doc_uuids)

        doc_ids = list(docs.values_list("id", flat=True))

        try:
            from .services.qa_chain import chat_with_documents
            answer, sources = chat_with_documents(question, doc_ids, chat_history)
        except Exception as e:
            logger.error("Chat failed: %s", e, exc_info=True)
            return Response(
                {"error": f"AI processing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Map sources to frontend format
        frontend_sources = []
        for src in sources:
            frontend_sources.append({
                "documentId": src.get("document_uuid", ""),
                "documentTitle": src.get("document_title", ""),
                "excerpt": src.get("excerpt", ""),
                "relevanceScore": src.get("relevance_score", 0),
            })

        return Response({
            "id": str(uuid_lib.uuid4()),
            "message": answer,
            "sources": frontend_sources,
            "conversationId": conversation_id,
            "tokensUsed": 0,
        })
