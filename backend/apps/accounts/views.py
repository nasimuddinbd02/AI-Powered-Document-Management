"""
Views for the accounts app.

Provides user registration, authentication, profile management,
role management, and audit log viewing.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import AuditLog, Permission, Role, UserRole
from .permissions import IsAdmin
from .serializers import (
    AdminUserSerializer,
    AuditLogSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PermissionSerializer,
    RegisterSerializer,
    RoleCreateUpdateSerializer,
    RoleSerializer,
    UserProfileUpdateSerializer,
    UserRoleSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# =============================================================================
# Auth Views
# =============================================================================


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.

    POST /api/v1/auth/register/
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        # Log the registration
        AuditLog.objects.create(
            user=user,
            action=AuditLog.ActionType.CREATE,
            resource_type="user",
            resource_id=str(user.id),
            details={"event": "registration"},
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "success": True,
                "message": "Registration successful.",
                "data": {
                    "user": user_data,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")


class LoginView(TokenObtainPairView):
    """
    Authenticate a user and return JWT tokens.

    POST /api/v1/auth/login/
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user_data = response.data.get("user")
            if user_data:
                try:
                    user = User.objects.get(id=user_data["id"])
                    AuditLog.objects.create(
                        user=user,
                        action=AuditLog.ActionType.LOGIN,
                        resource_type="user",
                        resource_id=str(user.id),
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    )
                except User.DoesNotExist:
                    pass
            response.data = {
                "success": True,
                "message": "Login successful.",
                "data": response.data,
            }
        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")


class CustomTokenRefreshView(TokenRefreshView):
    """
    Refresh an access token using a refresh token.

    POST /api/v1/auth/refresh/
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data = {
                "success": True,
                "message": "Token refreshed successfully.",
                "data": response.data,
            }
        return response


class LogoutView(APIView):
    """
    Blacklist the user's refresh token to log them out.

    POST /api/v1/auth/logout/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"success": False, "error": {"message": "Refresh token is required."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            AuditLog.objects.create(
                user=request.user,
                action=AuditLog.ActionType.LOGOUT,
                resource_type="user",
                resource_id=str(request.user.id),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            return Response(
                {"success": True, "message": "Logout successful."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning("Logout failed: %s", e)
            return Response(
                {"success": False, "error": {"message": "Invalid or expired token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @staticmethod
    def _get_client_ip(request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0].strip() if x_forwarded else request.META.get("REMOTE_ADDR")


# =============================================================================
# Profile Views
# =============================================================================


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.

    GET  /api/v1/auth/me/
    PUT  /api/v1/auth/me/
    PATCH /api/v1/auth/me/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserProfileUpdateSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response({"success": True, "data": serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "data": UserSerializer(request.user).data,
            }
        )


class ChangePasswordView(APIView):
    """
    Change the authenticated user's password.

    POST /api/v1/auth/change-password/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


# =============================================================================
# Admin Views
# =============================================================================


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin endpoint for managing users.

    GET    /api/v1/auth/admin/users/
    POST   /api/v1/auth/admin/users/
    GET    /api/v1/auth/admin/users/{id}/
    PUT    /api/v1/auth/admin/users/{id}/
    DELETE /api/v1/auth/admin/users/{id}/
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ["is_active", "is_staff", "department"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["date_joined", "email", "username"]

    @action(detail=True, methods=["post"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        """Activate or deactivate a user."""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        action_label = "activated" if user.is_active else "deactivated"
        return Response(
            {"success": True, "message": f"User {action_label} successfully."}
        )

    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        """Assign a role to a user."""
        user = self.get_object()
        role_id = request.data.get("role_id")
        if not role_id:
            return Response(
                {"success": False, "error": {"message": "role_id is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response(
                {"success": False, "error": {"message": "Role not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_role, created = UserRole.objects.get_or_create(
            user=user, role=role, defaults={"assigned_by": request.user}
        )
        if not created:
            return Response(
                {"success": False, "error": {"message": "User already has this role."}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {"success": True, "message": f"Role '{role.name}' assigned to {user.email}."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="remove-role")
    def remove_role(self, request, pk=None):
        """Remove a role from a user."""
        user = self.get_object()
        role_id = request.data.get("role_id")
        if not role_id:
            return Response(
                {"success": False, "error": {"message": "role_id is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        deleted, _ = UserRole.objects.filter(user=user, role_id=role_id).delete()
        if not deleted:
            return Response(
                {"success": False, "error": {"message": "User does not have this role."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "message": "Role removed successfully."})


class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD for roles.

    /api/v1/auth/admin/roles/
    """

    queryset = Role.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ["is_active"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RoleCreateUpdateSerializer
        return RoleSerializer


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List / retrieve permissions (read-only for admins).

    /api/v1/auth/admin/permissions/
    """

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    search_fields = ["codename", "name"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List / retrieve audit log entries (admin only).

    /api/v1/auth/admin/audit-log/
    """

    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ["action", "resource_type", "user"]
    search_fields = ["resource_id", "user__email"]
    ordering_fields = ["created_at"]
