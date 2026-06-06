"""
Views for the documents app.

Provides full CRUD for documents, version management, metadata,
tags, categories, and document access sharing.
"""

import logging

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AuditLog
from apps.accounts.permissions import IsOwnerOrAdmin

from .filters import DocumentFilter
from .models import (
    Category,
    Document,
    DocumentAccess,
    DocumentMetadata,
    DocumentTag,
    DocumentVersion,
    Tag,
)
from .serializers import (
    CategoryListSerializer,
    CategorySerializer,
    DocumentAccessSerializer,
    DocumentCreateSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentMetadataSerializer,
    DocumentUpdateSerializer,
    DocumentVersionSerializer,
    DocumentVersionUploadSerializer,
    TagSerializer,
)
from .services.storage import DocumentStorageService
from .services.versioning import DocumentVersioningService

logger = logging.getLogger(__name__)


# =============================================================================
# Document CRUD ViewSet
# =============================================================================


class DocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for documents.

    list:     GET    /api/v1/documents/
    create:   POST   /api/v1/documents/
    retrieve: GET    /api/v1/documents/{uuid}/
    update:   PUT    /api/v1/documents/{uuid}/
    partial:  PATCH  /api/v1/documents/{uuid}/
    destroy:  DELETE /api/v1/documents/{uuid}/
    """

    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DocumentFilter
    search_fields = ["title", "description", "original_filename"]
    ordering_fields = ["title", "created_at", "updated_at", "file_size"]
    ordering = ["-created_at"]
    lookup_field = "uuid"
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """
        Return documents the current user owns or has access to.
        Exclude soft-deleted documents.
        """
        user = self.request.user
        if user.is_staff:
            return Document.objects.filter(is_deleted=False).select_related(
                "owner", "category"
            ).prefetch_related("tags", "metadata")

        return Document.objects.filter(
            is_deleted=False
        ).filter(
            models_Q_owner_or_access(user)
        ).select_related("owner", "category").prefetch_related("tags", "metadata")

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        if self.action == "create":
            return DocumentCreateSerializer
        if self.action in ("update", "partial_update"):
            return DocumentUpdateSerializer
        return DocumentDetailSerializer

    def perform_create(self, serializer):
        document = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.ActionType.CREATE,
            resource_type="document",
            resource_id=str(document.uuid),
            details={"title": document.title},
            ip_address=_get_client_ip(self.request),
        )

    def perform_destroy(self, instance):
        """Soft-delete the document instead of hard delete."""
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.ActionType.DELETE,
            resource_type="document",
            resource_id=str(instance.uuid),
            details={"title": instance.title},
            ip_address=_get_client_ip(self.request),
        )

    # --- Custom Actions ---

    @action(detail=False, methods=["get"], url_path="recent")
    def recent(self, request):
        """Get recent documents for the dashboard."""
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        qs = self.get_queryset()[:limit]
        serializer = DocumentListSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        """Get high-level document statistics for the dashboard."""
        qs = self.get_queryset()
        total = qs.count()
        return Response({
            "success": True,
            "data": {
                "totalDocuments": total,
                "recentUploads": qs.filter(is_archived=False).count(),
                "aiSummaries": 0,
                "storageUsed": 0
            }
        })

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, uuid=None):
        """
        Download the current version of the document.

        GET /api/v1/documents/{uuid}/download/
        """
        document = self.get_object()
        storage = DocumentStorageService()
        file_obj = storage.retrieve_file(document.storage_path)
        if file_obj is None:
            raise Http404("File not found on storage.")

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ActionType.DOWNLOAD,
            resource_type="document",
            resource_id=str(document.uuid),
            ip_address=_get_client_ip(request),
        )

        import mimetypes
        content_type, _ = mimetypes.guess_type(document.original_filename or document.file.name)
        if not content_type:
            content_type = "application/octet-stream"

        response = FileResponse(
            file_obj,
            content_type=content_type,
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{document.original_filename or document.title}"'
        )
        return response

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, uuid=None):
        """Toggle archive status of a document."""
        document = self.get_object()
        document.is_archived = not document.is_archived
        document.save(update_fields=["is_archived"])
        label = "archived" if document.is_archived else "unarchived"
        return Response(
            {"success": True, "message": f"Document {label} successfully."}
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="versions",
        parser_classes=[MultiPartParser, FormParser],
    )
    def versions(self, request, uuid=None):
        """
        GET  — List version history.
        POST — Upload a new version.
        """
        document = self.get_object()
        versioning = DocumentVersioningService()

        if request.method == "GET":
            history = versioning.get_version_history(document)
            serializer = DocumentVersionSerializer(history, many=True)
            return Response({"success": True, "data": serializer.data})

        # POST — upload new version
        serializer = DocumentVersionUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            version = versioning.create_new_version(
                document=document,
                file=serializer.validated_data["file"],
                change_note=serializer.validated_data.get("change_note", ""),
                uploaded_by=request.user,
            )
        except ValueError as e:
            return Response(
                {"success": False, "error": {"message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"Version {version.version_number} uploaded.",
                "data": DocumentVersionSerializer(version).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="versions/(?P<version_number>[0-9]+)/restore")
    def restore_version(self, request, uuid=None, version_number=None):
        """
        Restore the document to a previous version.

        POST /api/v1/documents/{uuid}/versions/{version_number}/restore/
        """
        document = self.get_object()
        versioning = DocumentVersioningService()
        try:
            version = versioning.restore_version(
                document=document,
                version_number=int(version_number),
                restored_by=request.user,
            )
        except ValueError as e:
            return Response(
                {"success": False, "error": {"message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": f"Document restored to version {version_number}.",
                "data": DocumentVersionSerializer(version).data,
            }
        )

    @action(detail=True, methods=["get", "post", "delete"], url_path="metadata")
    def metadata(self, request, uuid=None):
        """
        GET    — List metadata for the document.
        POST   — Add a metadata entry.
        DELETE — Remove metadata by key (pass ?key=...).
        """
        document = self.get_object()

        if request.method == "GET":
            qs = document.metadata.all()
            serializer = DocumentMetadataSerializer(qs, many=True)
            return Response({"success": True, "data": serializer.data})

        if request.method == "POST":
            serializer = DocumentMetadataSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(document=document)
            return Response(
                {"success": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        # DELETE
        key = request.query_params.get("key")
        if not key:
            return Response(
                {"success": False, "error": {"message": "Query param 'key' is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = DocumentMetadata.objects.filter(document=document, key=key).delete()
        if not deleted:
            return Response(
                {"success": False, "error": {"message": f"Metadata key '{key}' not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "message": f"Metadata '{key}' deleted."})

    @action(detail=True, methods=["get", "post", "delete"], url_path="access")
    def access(self, request, uuid=None):
        """
        Manage document sharing / access.

        GET    — List current access records.
        POST   — Grant access to a user.
        DELETE — Revoke access (pass ?user_id=...).
        """
        document = self.get_object()

        if request.method == "GET":
            qs = document.access_records.select_related("user", "granted_by")
            serializer = DocumentAccessSerializer(qs, many=True)
            return Response({"success": True, "data": serializer.data})

        if request.method == "POST":
            serializer = DocumentAccessSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(document=document, granted_by=request.user)
            AuditLog.objects.create(
                user=request.user,
                action=AuditLog.ActionType.SHARE,
                resource_type="document",
                resource_id=str(document.uuid),
                details={
                    "shared_with": serializer.validated_data["user"].id,
                    "access_level": serializer.validated_data["access_level"],
                },
                ip_address=_get_client_ip(request),
            )
            return Response(
                {"success": True, "message": "Access granted.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        # DELETE
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"success": False, "error": {"message": "Query param 'user_id' is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = DocumentAccess.objects.filter(document=document, user_id=user_id).delete()
        if not deleted:
            return Response(
                {"success": False, "error": {"message": "Access record not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "message": "Access revoked."})


# =============================================================================
# Tag ViewSet
# =============================================================================


class TagViewSet(viewsets.ModelViewSet):
    """CRUD for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name"]
    ordering = ["name"]


# =============================================================================
# Category ViewSet
# =============================================================================


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for categories (hierarchical)."""

    queryset = Category.objects.select_related("parent").all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryListSerializer
        return CategorySerializer

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """Return the full category tree (root categories with nested children)."""
        roots = Category.objects.filter(parent__isnull=True)
        serializer = CategorySerializer(roots, many=True)
        return Response({"success": True, "data": serializer.data})


# =============================================================================
# Helpers
# =============================================================================


def models_Q_owner_or_access(user):
    """
    Build a Q object that matches documents the user owns or has access to.
    """
    from django.db.models import Q
    return Q(owner=user) | Q(access_records__user=user)


def _get_client_ip(request):
    """Extract client IP from request headers."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")
