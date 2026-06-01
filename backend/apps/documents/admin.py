"""
Admin configuration for the documents app.
"""

from django.contrib import admin

from .models import (
    Category,
    Document,
    DocumentAccess,
    DocumentMetadata,
    DocumentTag,
    DocumentVersion,
    Tag,
)


class DocumentMetadataInline(admin.TabularInline):
    model = DocumentMetadata
    extra = 0


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ("version_number", "file_size", "checksum", "uploaded_by", "created_at")


class DocumentTagInline(admin.TabularInline):
    model = DocumentTag
    extra = 0


class DocumentAccessInline(admin.TabularInline):
    model = DocumentAccess
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "uuid",
        "file_type",
        "file_size",
        "current_version",
        "owner",
        "is_archived",
        "is_deleted",
        "ocr_status",
        "ai_status",
        "created_at",
    )
    list_filter = ("file_type", "is_archived", "is_deleted", "ocr_status", "ai_status")
    search_fields = ("title", "description", "uuid")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("owner", "category")
    inlines = [DocumentMetadataInline, DocumentVersionInline, DocumentTagInline, DocumentAccessInline]
    date_hierarchy = "created_at"


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "file_size", "checksum", "uploaded_by", "created_at")
    list_filter = ("created_at",)
    raw_id_fields = ("document", "uploaded_by")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "created_at")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "created_at")
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(DocumentMetadata)
class DocumentMetadataAdmin(admin.ModelAdmin):
    list_display = ("document", "key", "value", "value_type")
    list_filter = ("value_type",)
    raw_id_fields = ("document",)


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "access_level", "granted_by", "created_at")
    list_filter = ("access_level",)
    raw_id_fields = ("document", "user", "granted_by")
