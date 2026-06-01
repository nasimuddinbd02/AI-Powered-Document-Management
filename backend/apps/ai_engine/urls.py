from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AISummaryViewSet, SummarizeDocumentView, AskQuestionView, ChatView

router = DefaultRouter()
router.register(r'summaries', AISummaryViewSet, basename='ai-summary')

urlpatterns = [
    path('', include(router.urls)),
    path('summarize/<uuid:uuid>/', SummarizeDocumentView.as_view(), name='summarize-document'),
    path('ask/', AskQuestionView.as_view(), name='ask-question'),
    path('chat/', ChatView.as_view(), name='chat'),
]
