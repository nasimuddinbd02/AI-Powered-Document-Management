"""
Custom pagination classes for the Document Management System.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class used across the API.

    Supports query-param customization of page size:
        ?page=1&page_size=20

    Includes total counts and navigation links in the response.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return a paginated response with metadata."""
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for endpoints that return larger result sets."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination for endpoints that return small result sets."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
