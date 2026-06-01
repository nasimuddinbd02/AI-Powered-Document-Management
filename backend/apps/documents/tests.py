"""
Tests for the documents app.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Document, DocumentVersion, Tag

User = get_user_model()


class DocumentModelTests(TestCase):
    """Tests for the Document model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="doc@example.com",
            username="docuser",
            password="TestPass123!",
        )
        self.document = Document.objects.create(
            title="Test Document",
            description="A test document.",
            file=SimpleUploadedFile("test.pdf", b"fake pdf content"),
            file_type=Document.FileType.PDF,
            file_size=1024,
            owner=self.user,
        )

    def test_document_creation(self):
        self.assertEqual(self.document.title, "Test Document")
        self.assertEqual(self.document.file_type, "pdf")
        self.assertEqual(self.document.current_version, 1)

    def test_str_representation(self):
        self.assertIn("Test Document", str(self.document))

    def test_uuid_is_unique(self):
        doc2 = Document.objects.create(
            title="Second Doc",
            file=SimpleUploadedFile("test2.pdf", b"fake content"),
            file_type=Document.FileType.PDF,
            file_size=512,
            owner=self.user,
        )
        self.assertNotEqual(self.document.uuid, doc2.uuid)

    def test_soft_delete(self):
        self.document.is_deleted = True
        self.document.save()
        self.assertTrue(self.document.is_deleted)


class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def test_hierarchy(self):
        parent = Category.objects.create(name="Engineering", slug="engineering")
        child = Category.objects.create(name="Backend", slug="backend", parent=parent)
        self.assertEqual(child.full_path, "Engineering > Backend")

    def test_str_representation(self):
        cat = Category.objects.create(name="Finance", slug="finance")
        self.assertEqual(str(cat), "Finance")


class TagModelTests(TestCase):
    """Tests for the Tag model."""

    def test_tag_creation(self):
        tag = Tag.objects.create(name="important", color="#FF0000")
        self.assertEqual(str(tag), "important")


class DocumentAPITests(TestCase):
    """Integration tests for document API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="api@example.com",
            username="apiuser",
            password="TestPass123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_document(self):
        file = SimpleUploadedFile(
            "test.txt", b"hello world", content_type="text/plain"
        )
        data = {
            "title": "API Test",
            "description": "Created via API",
            "file": file,
        }
        response = self.client.post("/api/v1/documents/", data, format="multipart")
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

    def test_list_documents(self):
        Document.objects.create(
            title="Listed Doc",
            file=SimpleUploadedFile("listed.txt", b"content"),
            file_type=Document.FileType.TXT,
            file_size=7,
            owner=self.user,
        )
        response = self.client.get("/api/v1/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tags_crud(self):
        response = self.client.post(
            "/api/v1/documents/tags/",
            {"name": "urgent", "color": "#FF0000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get("/api/v1/documents/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
