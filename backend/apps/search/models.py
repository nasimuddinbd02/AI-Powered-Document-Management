"""
Search app models.

Stores search-related data such as search history and saved searches.
"""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class SearchHistory(TimeStampedModel):
    """
    Stores user search queries for analytics and recent-search suggestions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_history",
        help_text="User who performed the search.",
    )
    query = models.CharField(
        max_length=500,
        help_text="The search query string.",
    )
    search_type = models.CharField(
        max_length=20,
        choices=[
            ("fulltext", "Full-Text"),
            ("semantic", "Semantic"),
            ("hybrid", "Hybrid"),
        ],
        default="fulltext",
        help_text="Type of search performed.",
    )
    results_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of results returned.",
    )
    filters_applied = models.JSONField(
        blank=True,
        null=True,
        help_text="Filters applied during the search (JSON).",
    )

    class Meta:
        db_table = "search_history"
        verbose_name = "Search History"
        verbose_name_plural = "Search History"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email}: '{self.query}' ({self.search_type})"


class SavedSearch(TimeStampedModel):
    """
    Allows users to save frequently-used search queries.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
        help_text="User who saved the search.",
    )
    name = models.CharField(
        max_length=100,
        help_text="User-defined name for the saved search.",
    )
    query = models.CharField(
        max_length=500,
        help_text="The search query string.",
    )
    search_type = models.CharField(
        max_length=20,
        choices=[
            ("fulltext", "Full-Text"),
            ("semantic", "Semantic"),
            ("hybrid", "Hybrid"),
        ],
        default="fulltext",
    )
    filters = models.JSONField(
        blank=True,
        null=True,
        help_text="Saved filter parameters (JSON).",
    )

    class Meta:
        db_table = "saved_searches"
        verbose_name = "Saved Search"
        verbose_name_plural = "Saved Searches"
        ordering = ["-created_at"]
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user.email}: {self.name}"
