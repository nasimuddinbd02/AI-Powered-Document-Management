"""
URL routes for the search app.

All routes are relative to /api/v1/search/.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FullTextSearchView,
    SavedSearchViewSet,
    SearchHistoryViewSet,
    SearchView,
    SemanticSearchView,
)

app_name = "search"

router = DefaultRouter()
router.register(r"history", SearchHistoryViewSet, basename="search-history")
router.register(r"saved", SavedSearchViewSet, basename="saved-searches")

urlpatterns = [
    path("", SearchView.as_view(), name="search"),
    path("fulltext/", FullTextSearchView.as_view(), name="fulltext-search"),
    path("semantic/", SemanticSearchView.as_view(), name="semantic-search"),
    path("", include(router.urls)),
]
