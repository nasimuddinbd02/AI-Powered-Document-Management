"""
Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, Permission, Role, RolePermission, UserRole

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "department",
        "is_staff",
        "is_active",
        "is_verified",
    )
    list_filter = ("is_staff", "is_active", "is_verified", "department")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("department", "avatar", "phone", "bio", "is_verified"),
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("email", "department", "phone"),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "created_at")
    search_fields = ("codename", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_by", "created_at")
    list_filter = ("role",)
    raw_id_fields = ("user", "assigned_by")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission", "created_at")
    list_filter = ("role",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "resource_type", "resource_id", "ip_address", "created_at")
    list_filter = ("action", "resource_type")
    search_fields = ("user__email", "resource_id")
    readonly_fields = ("user", "action", "resource_type", "resource_id", "details", "ip_address", "user_agent", "created_at")
    date_hierarchy = "created_at"
