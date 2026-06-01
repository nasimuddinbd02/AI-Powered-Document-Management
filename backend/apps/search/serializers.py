"""
Serializers for the search app.
"""

from rest_framework import serializers

from apps.documents.serializers import DocumentListSerializer

from .models import SavedSearch, SearchHistory


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for incoming search requests."""

    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Search query string.",
    )
    search_type = serializers.ChoiceField(
        choices=["fulltext", "semantic", "hybrid"],
        default="fulltext",
        help_text="Type of search to perform.",
    )
    file_type = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False)
    tag_id = serializers.IntegerField(required=False)
    is_archived = serializers.BooleanField(required=False)
    created_after = serializers.DateTimeField(required=False)
    created_before = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results."""

    document = DocumentListSerializer()
    score = serializers.FloatField(required=False, default=0.0)
    highlight = serializers.CharField(required=False, default="")


class SemanticSearchResultSerializer(serializers.Serializer):
    """Serializer for semantic search results (includes chunk info)."""

    document_id = serializers.IntegerField()
    document_uuid = serializers.CharField()
    document_title = serializers.CharField()
    chunk_text = serializers.CharField()
    chunk_index = serializers.IntegerField()
    score = serializers.FloatField()


class SearchHistorySerializer(serializers.ModelSerializer):
    """Serializer for search history entries."""

    class Meta:
        model = SearchHistory
        fields = ("id", "query", "search_type", "results_count", "filters_applied", "created_at")
        read_only_fields = fields


class SavedSearchSerializer(serializers.ModelSerializer):
    """Serializer for saved searches."""

    class Meta:
        model = SavedSearch
        fields = ("id", "name", "query", "search_type", "filters", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
