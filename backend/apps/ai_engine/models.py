import uuid
from django.db import models
from apps.documents.models import Document, DocumentVersion

class AISummary(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ai_summaries')
    version_number = models.IntegerField(null=True, blank=True)
    summary = models.TextField()
    key_topics = models.JSONField(default=list)
    entities = models.JSONField(default=dict)
    model_used = models.CharField(max_length=100)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.document.title}"

class DocumentEmbedding(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='embeddings')
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    # Storing embeddings as JSON to support SQLite in dev. 
    # For production with pgvector, this would be a VectorField.
    embedding = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"Embedding chunk {self.chunk_index} for {self.document.title}"
