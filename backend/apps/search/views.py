"""
Views for the search app.

Provides full-text, semantic, and hybrid search endpoints, plus
search history and saved search management.
"""

import logging

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.serializers import DocumentListSerializer

from .models import SavedSearch, SearchHistory
from .serializers import (
    SavedSearchSerializer,
    SearchHistorySerializer,
    SearchQuerySerializer,
    SemanticSearchResultSerializer,
)
from .services.fulltext import FullTextSearchService
from .services.semantic import SemanticSearchService

logger = logging.getLogger(__name__)


class SearchView(APIView):
    """
    Unified search endpoint supporting full-text, semantic, and hybrid search.

    POST /api/v1/search/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["query"]
        search_type = data.get("search_type", "fulltext")
        limit = data.get("limit", 20)

        filters = {
            k: v
            for k, v in data.items()
            if k not in ("query", "search_type", "limit") and v is not None
        }

        try:
            if search_type == "fulltext":
                results = self._fulltext_search(query, request.user, filters, limit)
            elif search_type == "semantic":
                results = self._semantic_search(query, request.user, limit)
            elif search_type == "hybrid":
                results = self._hybrid_search(query, request.user, filters, limit)
            else:
                results = []
        except Exception as e:
            logger.error("Search error: %s", e, exc_info=True)
            return Response(
                {"success": False, "error": {"message": "Search failed. Please try again."}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Record in search history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            search_type=search_type,
            results_count=len(results) if isinstance(results, list) else results.count() if hasattr(results, 'count') else 0,
            filters_applied=filters or None,
        )

        # Serialize results
        if search_type == "semantic":
            result_data = SemanticSearchResultSerializer(results, many=True).data
        else:
            result_data = DocumentListSerializer(results, many=True).data

        return Response({
            "success": True,
            "data": {
                "query": query,
                "search_type": search_type,
                "count": len(result_data),
                "results": result_data,
            },
        })

    def _fulltext_search(self, query, user, filters, limit):
        service = FullTextSearchService()
        return service.search_with_ranking(query, user=user, filters=filters, limit=limit)

    def _semantic_search(self, query, user, limit):
        service = SemanticSearchService()
        return service.search(query, user=user, top_k=limit)

    def _hybrid_search(self, query, user, filters, limit):
        """
        Combine full-text and semantic results.

        Full-text results are returned first, then semantic results
        that weren't already in the full-text set.
        """
        ft_service = FullTextSearchService()
        ft_results = list(ft_service.search_with_ranking(
            query, user=user, filters=filters, limit=limit
        ))

        try:
            sem_service = SemanticSearchService()
            sem_results = sem_service.search(query, user=user, top_k=limit)
        except Exception as e:
            logger.warning("Semantic search unavailable for hybrid: %s", e)
            sem_results = []

        # Merge: add semantic results whose documents aren't in full-text results
        ft_doc_ids = {doc.id for doc in ft_results}
        for sem_item in sem_results:
            doc_id = sem_item.get("document_id")
            if doc_id and doc_id not in ft_doc_ids:
                from apps.documents.models import Document
                try:
                    doc = Document.objects.get(id=doc_id)
                    ft_results.append(doc)
                    ft_doc_ids.add(doc_id)
                except Document.DoesNotExist:
                    pass

        return ft_results[:limit]


class FullTextSearchView(APIView):
    """
    Dedicated full-text search endpoint.

    POST /api/v1/search/fulltext/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = FullTextSearchService()
        filters = {
            k: v
            for k, v in data.items()
            if k not in ("query", "search_type", "limit") and v is not None
        }

        results = service.search_with_ranking(
            data["query"],
            user=request.user,
            filters=filters,
            limit=data.get("limit", 20),
        )

        return Response({
            "success": True,
            "data": {
                "query": data["query"],
                "count": len(results),
                "results": DocumentListSerializer(results, many=True).data,
            },
        })


class SemanticSearchView(APIView):
    """
    Dedicated semantic search endpoint.

    POST /api/v1/search/semantic/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SearchQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = SemanticSearchService()
        try:
            results = service.search(
                data["query"],
                user=request.user,
                top_k=data.get("limit", 10),
            )
        except Exception as e:
            logger.error("Semantic search failed: %s", e)
            return Response(
                {"success": False, "error": {"message": "Semantic search is unavailable."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            "success": True,
            "data": {
                "query": data["query"],
                "count": len(results),
                "results": SemanticSearchResultSerializer(results, many=True).data,
            },
        })


class SearchHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View and manage search history.

    GET /api/v1/search/history/
    """

    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        """Clear all search history for the current user."""
        count, _ = SearchHistory.objects.filter(user=request.user).delete()
        return Response(
            {"success": True, "message": f"Cleared {count} search history entries."}
        )


class SavedSearchViewSet(viewsets.ModelViewSet):
    """
    CRUD for saved searches.

    /api/v1/search/saved/
    """

    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
