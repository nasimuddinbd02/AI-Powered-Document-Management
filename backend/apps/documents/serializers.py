"""
Serializers for the documents app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Category,
    Document,
    DocumentAccess,
    DocumentMetadata,
    DocumentTag,
    DocumentVersion,
    Tag,
)

User = get_user_model()


# =============================================================================
# Tag / Category Serializers
# =============================================================================


class TagSerializer(serializers.ModelSerializer):
    """Serializer for document tags."""

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "created_at")
        read_only_fields = ("id", "created_at")


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories."""

    full_path = serializers.CharField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "parent", "full_path", "children", "created_at")
        read_only_fields = ("id", "created_at")

    def get_children(self, obj):
        """Recursively serialize child categories."""
        children = obj.children.all()
        if children.exists():
            return CategorySerializer(children, many=True).data
        return []


class CategoryListSerializer(serializers.ModelSerializer):
    """Flat category serializer for list views (no recursion)."""

    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "parent", "full_path")
        read_only_fields = ("id",)


# =============================================================================
# Document Metadata Serializer
# =============================================================================


class DocumentMetadataSerializer(serializers.ModelSerializer):
    """Serializer for document metadata key-value pairs."""

    class Meta:
        model = DocumentMetadata
        fields = ("id", "key", "value", "value_type", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# =============================================================================
# Document Version Serializer
# =============================================================================


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions."""

    uploaded_by_email = serializers.CharField(
        source="uploaded_by.email", read_only=True, default=""
    )

    class Meta:
        model = DocumentVersion
        fields = (
            "id",
            "version_number",
            "file",
            "file_size",
            "change_note",
            "checksum",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
        )
        read_only_fields = ("id", "version_number", "file_size", "checksum", "uploaded_by", "created_at")


# =============================================================================
# Document Access Serializer
# =============================================================================


class DocumentAccessSerializer(serializers.ModelSerializer):
    """Serializer for document access records."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    granted_by_email = serializers.CharField(
        source="granted_by.email", read_only=True, default=""
    )

    class Meta:
        model = DocumentAccess
        fields = (
            "id",
            "document",
            "user",
            "user_email",
            "access_level",
            "granted_by",
            "granted_by_email",
            "created_at",
        )
        read_only_fields = ("id", "granted_by", "created_at")


# =============================================================================
# Document Serializers
# =============================================================================


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for document list views.

    Includes tags, category, and owner info but omits large fields
    like extracted_text.
    """

    owner_email = serializers.CharField(source="owner.email", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default="")
    tags = TagSerializer(many=True, read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "uuid",
            "title",
            "description",
            "file_type",
            "file_size",
            "file_size_display",
            "original_filename",
            "current_version",
            "owner",
            "owner_email",
            "owner_name",
            "category",
            "category_name",
            "tags",
            "is_archived",
            "ocr_status",
            "ai_status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_file_size_display(self, obj):
        from apps.common.utils import format_file_size
        return format_file_size(obj.file_size)


class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for document detail views.

    Includes metadata, versions, access records, and extracted text.
    """

    owner_email = serializers.CharField(source="owner.email", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default="")
    tags = TagSerializer(many=True, read_only=True)
    metadata = DocumentMetadataSerializer(many=True, read_only=True)
    versions = DocumentVersionSerializer(many=True, read_only=True)
    access_records = DocumentAccessSerializer(many=True, read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "uuid",
            "title",
            "description",
            "file",
            "file_type",
            "file_size",
            "file_size_display",
            "storage_path",
            "original_filename",
            "current_version",
            "owner",
            "owner_email",
            "owner_name",
            "category",
            "category_name",
            "tags",
            "is_archived",
            "is_deleted",
            "ocr_status",
            "ai_status",
            "extracted_text",
            "metadata",
            "versions",
            "access_records",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_file_size_display(self, obj):
        from apps.common.utils import format_file_size
        return format_file_size(obj.file_size)


class DocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new document via file upload.
    """

    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="List of tag IDs to attach.",
    )
    metadata_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text="List of {key, value, value_type} dicts.",
    )

    class Meta:
        model = Document
        fields = (
            "title",
            "description",
            "file",
            "category",
            "tag_ids",
            "metadata_items",
        )

    def validate_file(self, value):
        """Validate the uploaded file size and type."""
        from apps.common.utils import validate_file_size, validate_file_type
        try:
            validate_file_size(value)
            validate_file_type(value.name)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        from apps.documents.services.upload import DocumentUploadService

        tag_ids = validated_data.pop("tag_ids", [])
        metadata_items = validated_data.pop("metadata_items", [])
        request = self.context["request"]

        service = DocumentUploadService()
        document = service.create_document(
            file=validated_data["file"],
            title=validated_data["title"],
            description=validated_data.get("description", ""),
            category=validated_data.get("category"),
            owner=request.user,
            tag_ids=tag_ids,
            metadata_items=metadata_items,
        )
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating document metadata (not the file)."""

    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Document
        fields = ("title", "description", "category", "is_archived", "tag_ids")

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tag_ids is not None:
            # Replace tags
            DocumentTag.objects.filter(document=instance).delete()
            for tid in tag_ids:
                DocumentTag.objects.create(document=instance, tag_id=tid)

        return instance


class DocumentVersionUploadSerializer(serializers.Serializer):
    """Serializer for uploading a new version of an existing document."""

    file = serializers.FileField(required=True)
    change_note = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_file(self, value):
        from apps.common.utils import validate_file_size, validate_file_type
        try:
            validate_file_size(value)
            validate_file_type(value.name)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value
