from rest_framework import serializers
from .models import AISummary

class AISummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = AISummary
        fields = ['id', 'document', 'version_number', 'summary', 'key_topics', 'entities', 'model_used', 'generated_at']
        read_only_fields = ['id', 'generated_at']

class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    document_ids = serializers.ListField(child=serializers.UUIDField(), required=False)

class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField()

class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    document_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    chat_history = ChatMessageSerializer(many=True, required=False, default=list)
