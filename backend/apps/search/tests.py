"""
Tests for the search app.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.documents.models import Document

from .models import SavedSearch, SearchHistory
from .services.fulltext import FullTextSearchService

User = get_user_model()


class FullTextSearchServiceTests(TestCase):
    """Tests for the full-text search service."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="search@example.com",
            username="searchuser",
            password="TestPass123!",
        )
        self.doc1 = Document.objects.create(
            title="Machine Learning Fundamentals",
            description="Introduction to ML concepts.",
            file=SimpleUploadedFile("ml.pdf", b"content"),
            file_type=Document.FileType.PDF,
            file_size=1024,
            owner=self.user,
            extracted_text="Machine learning is a subset of artificial intelligence.",
        )
        self.doc2 = Document.objects.create(
            title="Django REST Framework Guide",
            description="Building APIs with Django.",
            file=SimpleUploadedFile("drf.pdf", b"content"),
            file_type=Document.FileType.PDF,
            file_size=2048,
            owner=self.user,
            extracted_text="Django REST framework provides powerful serialization.",
        )
        self.service = FullTextSearchService()

    def test_search_by_title(self):
        results = self.service.search("Machine Learning", user=self.user)
        self.assertTrue(any(d.id == self.doc1.id for d in results))

    def test_search_by_extracted_text(self):
        results = self.service.search("artificial intelligence", user=self.user)
        self.assertTrue(any(d.id == self.doc1.id for d in results))

    def test_empty_query(self):
        results = self.service.search("", user=self.user)
        self.assertEqual(results.count(), 0)

    def test_no_results(self):
        results = self.service.search("quantum physics", user=self.user)
        self.assertEqual(len(list(results)), 0)


class SearchAPITests(TestCase):
    """Integration tests for search API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="searchapi@example.com",
            username="searchapiuser",
            password="TestPass123!",
        )
        self.client.force_authenticate(user=self.user)

        Document.objects.create(
            title="Searchable Document",
            description="This document is searchable.",
            file=SimpleUploadedFile("search.txt", b"content"),
            file_type=Document.FileType.TXT,
            file_size=7,
            owner=self.user,
        )

    def test_unified_search(self):
        response = self.client.post(
            "/api/v1/search/",
            {"query": "Searchable", "search_type": "fulltext"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_fulltext_search(self):
        response = self.client.post(
            "/api/v1/search/fulltext/",
            {"query": "Searchable"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_history(self):
        # Perform a search
        self.client.post(
            "/api/v1/search/",
            {"query": "test", "search_type": "fulltext"},
            format="json",
        )
        # Check history
        response = self.client.get("/api/v1/search/history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SearchModelTests(TestCase):
    """Tests for search models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="model@example.com",
            username="modeluser",
            password="TestPass123!",
        )

    def test_search_history_creation(self):
        history = SearchHistory.objects.create(
            user=self.user,
            query="test search",
            search_type="fulltext",
            results_count=5,
        )
        self.assertIn("test search", str(history))

    def test_saved_search_creation(self):
        saved = SavedSearch.objects.create(
            user=self.user,
            name="My Search",
            query="important documents",
            search_type="fulltext",
        )
        self.assertIn("My Search", str(saved))
