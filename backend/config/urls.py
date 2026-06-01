"""
URL configuration for AI-Powered Document Management System.

All API endpoints are versioned under /api/v1/.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("documents/", include("apps.documents.urls")),
    path("search/", include("apps.search.urls")),
    # path("ai/", include("apps.ai_engine.urls")),
]

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/", include((api_v1_patterns, "api-v1"))),
    # OpenAPI Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
