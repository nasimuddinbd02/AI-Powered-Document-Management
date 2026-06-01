"""
URL routes for the documents app.

All routes are relative to /api/v1/documents/.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, DocumentViewSet, TagViewSet

app_name = "documents"

router = DefaultRouter()
router.register(r"", DocumentViewSet, basename="documents")

# Separate routers for tags and categories so they don't conflict
tag_router = DefaultRouter()
tag_router.register(r"", TagViewSet, basename="tags")

category_router = DefaultRouter()
category_router.register(r"", CategoryViewSet, basename="categories")

urlpatterns = [
    path("tags/", include(tag_router.urls)),
    path("categories/", include(category_router.urls)),
    path("", include(router.urls)),
]
