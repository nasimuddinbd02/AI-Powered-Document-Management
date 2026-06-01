"""
Account models for the AI-Powered Document Management System.

Defines a custom User model, Role-based access control with Permissions,
and the through tables for M2M relationships.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimeStampedModel


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds department, avatar, and other profile fields.
    """

    email = models.EmailField(
        unique=True,
        help_text="User's email address. Used for login.",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Department the user belongs to.",
    )
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
        help_text="User's profile picture.",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="User's phone number.",
    )
    bio = models.TextField(
        blank=True,
        default="",
        help_text="Short user biography.",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified.",
    )

    # Use email for authentication instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def full_name(self):
        """Return the user's full name."""
        return self.get_full_name() or self.username

    def get_roles(self):
        """Return all roles assigned to this user."""
        return Role.objects.filter(userrole__user=self)

    def has_role(self, role_name):
        """Check whether the user has a specific role."""
        return self.userrole_set.filter(role__name=role_name).exists()

    def get_all_permissions_list(self):
        """Return a flat list of all permission codenames for the user."""
        return list(
            Permission.objects.filter(
                rolepermission__role__userrole__user=self
            ).values_list("codename", flat=True).distinct()
        )


class Role(TimeStampedModel):
    """
    Represents a role that can be assigned to users.

    Roles group permissions together for easier management.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique name for the role.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this role's purpose.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role is currently active.",
    )

    class Meta:
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(TimeStampedModel):
    """
    Represents a fine-grained permission that can be assigned to roles.
    """

    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Machine-readable permission identifier, e.g. 'document.create'.",
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable permission name.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of what this permission allows.",
    )

    class Meta:
        db_table = "permissions"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ["codename"]

    def __str__(self):
        return f"{self.codename} — {self.name}"


class UserRole(TimeStampedModel):
    """
    Through table linking Users to Roles.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="userrole_set",
        help_text="The user this role is assigned to.",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="userrole_set",
        help_text="The role assigned to the user.",
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_roles",
        help_text="The admin who assigned this role.",
    )

    class Meta:
        db_table = "user_roles"
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user.email} → {self.role.name}"


class RolePermission(TimeStampedModel):
    """
    Through table linking Roles to Permissions.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="rolepermission_set",
        help_text="The role this permission belongs to.",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="rolepermission_set",
        help_text="The permission granted to the role.",
    )

    class Meta:
        db_table = "role_permissions"
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name} → {self.permission.codename}"


class AuditLog(TimeStampedModel):
    """
    Records user actions for auditing purposes.
    """

    class ActionType(models.TextChoices):
        CREATE = "CREATE", "Create"
        READ = "READ", "Read"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        DOWNLOAD = "DOWNLOAD", "Download"
        SHARE = "SHARE", "Share"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="The user who performed the action.",
    )
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        help_text="Type of action performed.",
    )
    resource_type = models.CharField(
        max_length=50,
        help_text="Type of resource acted upon, e.g. 'document', 'user'.",
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Identifier of the resource acted upon.",
    )
    details = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional details about the action (JSON).",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which the action was performed.",
    )
    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="User-Agent string from the request.",
    )

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.resource_type}:{self.resource_id}"
