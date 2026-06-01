import logging
from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AISummary
from .serializers import AISummarySerializer, AskQuestionSerializer, ChatRequestSerializer
from apps.documents.models import Document
from .tasks import generate_summary_task
from .services.qa_chain import answer_question, chat_with_documents

logger = logging.getLogger(__name__)

class AISummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AISummary.objects.all()
    serializer_class = AISummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(document__uploaded_by=self.request.user)

class SummarizeDocumentView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        try:
            document = Document.objects.get(uuid=uuid, uploaded_by=request.user)
            # Dispatch Celery task
            task = generate_summary_task.delay(document.id)
            return Response({'status': 'processing', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

class AskQuestionView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AskQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            doc_uuids = serializer.validated_data.get('document_ids', [])
            
            # Fetch doc ids based on user permission and uuids
            docs = Document.objects.filter(uploaded_by=request.user)
            if doc_uuids:
                docs = docs.filter(uuid__in=doc_uuids)
            
            doc_ids = list(docs.values_list('id', flat=True))
            
            answer, sources = answer_question(question, doc_ids)
            return Response({
                'answer': answer,
                'sources': sources
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            doc_uuids = serializer.validated_data.get('document_ids', [])
            chat_history = serializer.validated_data.get('chat_history', [])
            
            docs = Document.objects.filter(uploaded_by=request.user)
            if doc_uuids:
                docs = docs.filter(uuid__in=doc_uuids)
            
            doc_ids = list(docs.values_list('id', flat=True))
            
            answer, sources = chat_with_documents(question, doc_ids, chat_history)
            return Response({
                'answer': answer,
                'sources': sources
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
