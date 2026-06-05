"""
Full-text search service.

Performs keyword-based search over documents using Django ORM queries.
Falls back to basic icontains when PostgreSQL full-text search is unavailable
(e.g. on SQLite in development).
"""

import logging

from django.db.models import Q, Value
from django.db.models.functions import Concat

from apps.documents.models import Document

logger = logging.getLogger(__name__)


class FullTextSearchService:
    """
    Provides full-text search across documents.

    Searches over title, description, extracted_text, original_filename,
    metadata values, and tag names.
    """

    def search(self, query, user=None, filters=None, limit=50):
        """
        Execute a full-text search.

        Args:
            query: The search string.
            user: Optional user to scope results (ownership / access).
            filters: Optional dict of filter parameters.
            limit: Maximum number of results.

        Returns:
            QuerySet of matching Documents.
        """
        if not query or not query.strip():
            return Document.objects.none()

        filters = filters or {}
        qs = Document.objects.filter(is_deleted=False)

        # Scope to user's accessible documents
        if user and not user.is_staff:
            qs = qs.filter(Q(owner=user) | Q(access_records__user=user))

        # Build the search query
        search_q = self._build_search_query(query.strip())
        qs = qs.filter(search_q)

        # Apply additional filters
        qs = self._apply_filters(qs, filters)

        # Deduplicate (can happen with M2M joins)
        qs = qs.distinct()

        return qs.select_related("owner", "category").prefetch_related("tags")[:limit]

    def _build_search_query(self, query):
        """Build a Q object for searching across multiple fields using OR logic."""
        terms = query.split()
        combined_q = Q()
        
        if not terms:
            return combined_q

        for term in terms:
            term_q = (
                Q(title__icontains=term)
                | Q(description__icontains=term)
                | Q(extracted_text__icontains=term)
                | Q(original_filename__icontains=term)
                | Q(metadata__value__icontains=term)
                | Q(tags__name__icontains=term)
            )
            combined_q |= term_q

        return combined_q

    def _apply_filters(self, qs, filters):
        """Apply additional filters to the queryset."""
        if "file_type" in filters:
            qs = qs.filter(file_type=filters["file_type"])
        if "category_id" in filters:
            qs = qs.filter(category_id=filters["category_id"])
        if "tag_id" in filters:
            qs = qs.filter(tags__id=filters["tag_id"])
        if "is_archived" in filters:
            qs = qs.filter(is_archived=filters["is_archived"])
        if "created_after" in filters:
            qs = qs.filter(created_at__gte=filters["created_after"])
        if "created_before" in filters:
            qs = qs.filter(created_at__lte=filters["created_before"])
        if "owner_id" in filters:
            qs = qs.filter(owner_id=filters["owner_id"])
        return qs

    def search_with_ranking(self, query, user=None, filters=None, limit=50):
        """
        Search with basic relevance ranking.

        Prioritises title matches over description, then extracted_text.

        Returns:
            list[dict]: Ranked results with score hints.
        """
        results = self.search(query, user=user, filters=filters, limit=limit * 2)
        scored = []
        query_lower = query.lower()

        for doc in results:
            score = 1.0
            
            # 1. Exact phrase match gets a big boost
            if doc.title and query_lower in doc.title.lower():
                score += 20
            if doc.description and query_lower in doc.description.lower():
                score += 10
            if doc.extracted_text and query_lower in doc.extracted_text.lower():
                score += 5

            # 2. Individual term matching
            terms = query_lower.split()
            for term in terms:
                if doc.title and term in doc.title.lower():
                    score += 10
                if doc.description and term in doc.description.lower():
                    score += 5
                if doc.original_filename and term in doc.original_filename.lower():
                    score += 10
                if doc.extracted_text and term in doc.extracted_text.lower():
                    score += 2

            if score >= 1.0:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored[:limit]]
