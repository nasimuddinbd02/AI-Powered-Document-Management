"""
Tests for the accounts app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import AuditLog, Permission, Role, UserRole

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            department="Engineering",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.department, "Engineering")
        self.assertTrue(self.user.check_password("TestPass123!"))

    def test_full_name(self):
        self.assertEqual(self.user.full_name, "Test User")

    def test_str_representation(self):
        self.assertIn("test@example.com", str(self.user))

    def test_has_role(self):
        role = Role.objects.create(name="editor", description="Can edit documents")
        UserRole.objects.create(user=self.user, role=role)
        self.assertTrue(self.user.has_role("editor"))
        self.assertFalse(self.user.has_role("admin"))


class RegisterViewTests(TestCase):
    """Tests for user registration."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("accounts:register")

    def test_register_success(self):
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongP@ss123!",
            "password_confirm": "StrongP@ss123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("tokens", response.data["data"])

    def test_register_password_mismatch(self):
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongP@ss123!",
            "password_confirm": "DifferentP@ss!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email="dup@example.com", username="dup", password="TestPass123!"
        )
        data = {
            "email": "dup@example.com",
            "username": "dup2",
            "first_name": "Dup",
            "last_name": "User",
            "password": "StrongP@ss123!",
            "password_confirm": "StrongP@ss123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class LoginViewTests(TestCase):
    """Tests for user login."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            email="login@example.com",
            username="loginuser",
            password="TestPass123!",
        )

    def test_login_success(self):
        data = {"email": "login@example.com", "password": "TestPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_login_wrong_password(self):
        data = {"email": "login@example.com", "password": "WrongPass!"}
        response = self.client.post(self.url, data, format="json")
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


class ProfileViewTests(TestCase):
    """Tests for user profile."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@example.com",
            username="profileuser",
            password="TestPass123!",
            first_name="Profile",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("accounts:user-profile")

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "profile@example.com")

    def test_update_profile(self):
        response = self.client.patch(
            self.url, {"department": "Research"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.department, "Research")


class RoleModelTests(TestCase):
    """Tests for Role and Permission models."""

    def test_create_role_with_permission(self):
        role = Role.objects.create(name="viewer", description="Read-only access")
        perm = Permission.objects.create(codename="document.read", name="Read Document")
        from .models import RolePermission
        RolePermission.objects.create(role=role, permission=perm)

        self.assertEqual(role.rolepermission_set.count(), 1)
        self.assertEqual(str(role), "viewer")
