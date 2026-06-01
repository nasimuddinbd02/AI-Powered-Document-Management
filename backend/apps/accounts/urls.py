"""
URL routes for the accounts app.

All routes are relative to /api/v1/auth/.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminUserViewSet,
    AuditLogViewSet,
    ChangePasswordView,
    CustomTokenRefreshView,
    LoginView,
    LogoutView,
    PermissionViewSet,
    RegisterView,
    RoleViewSet,
    UserProfileView,
)

app_name = "accounts"

# Admin routers
admin_router = DefaultRouter()
admin_router.register(r"users", AdminUserViewSet, basename="admin-users")
admin_router.register(r"roles", RoleViewSet, basename="admin-roles")
admin_router.register(r"permissions", PermissionViewSet, basename="admin-permissions")
admin_router.register(r"audit-log", AuditLogViewSet, basename="admin-audit-log")

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Profile
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # Admin
    path("admin/", include(admin_router.urls)),
]
