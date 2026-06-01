"""
Django-filter FilterSets for the documents app.
"""

import django_filters

from .models import Document


class DocumentFilter(django_filters.FilterSet):
    """
    Filter set for querying documents.

    Supports filtering by file type, category, tag, owner, archive
    status, date range, and text search.
    """

    title = django_filters.CharFilter(lookup_expr="icontains")
    description = django_filters.CharFilter(lookup_expr="icontains")
    file_type = django_filters.ChoiceFilter(choices=Document.FileType.choices)
    category = django_filters.NumberFilter(field_name="category__id")
    category_slug = django_filters.CharFilter(field_name="category__slug")
    tag = django_filters.NumberFilter(field_name="tags__id")
    tag_name = django_filters.CharFilter(field_name="tags__name", lookup_expr="iexact")
    owner = django_filters.NumberFilter(field_name="owner__id")
    is_archived = django_filters.BooleanFilter()
    ocr_status = django_filters.ChoiceFilter(choices=Document.OCRStatus.choices)
    ai_status = django_filters.ChoiceFilter(choices=Document.AIStatus.choices)
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    min_size = django_filters.NumberFilter(field_name="file_size", lookup_expr="gte")
    max_size = django_filters.NumberFilter(field_name="file_size", lookup_expr="lte")

    class Meta:
        model = Document
        fields = [
            "title",
            "description",
            "file_type",
            "category",
            "category_slug",
            "tag",
            "tag_name",
            "owner",
            "is_archived",
            "ocr_status",
            "ai_status",
            "created_after",
            "created_before",
            "min_size",
            "max_size",
        ]
