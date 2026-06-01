"""
Serializers for the accounts app.

Handles user registration, authentication, profile management, and roles.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AuditLog, Permission, Role, RolePermission, UserRole

User = get_user_model()


# =============================================================================
# Auth Serializers
# =============================================================================


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "department",
            "phone",
        )

    def validate(self, attrs):
        """Ensure the two password fields match."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create a new user with a hashed password."""
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
            department=validated_data.get("department", ""),
            phone=validated_data.get("phone", ""),
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes extra user info in the
    token claims and the response body.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["email"] = user.email
        token["username"] = user.username
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response body
        data["user"] = UserSerializer(self.user).data
        return data


# =============================================================================
# User Serializers
# =============================================================================


class UserSerializer(serializers.ModelSerializer):
    """Read-only user serializer with computed fields."""

    full_name = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "department",
            "avatar",
            "phone",
            "bio",
            "is_verified",
            "is_active",
            "date_joined",
            "last_login",
            "roles",
        )
        read_only_fields = (
            "id",
            "email",
            "is_verified",
            "is_active",
            "date_joined",
            "last_login",
        )

    def get_roles(self, obj):
        """Return a list of role names assigned to the user."""
        return list(
            obj.userrole_set.select_related("role")
            .values_list("role__name", flat=True)
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "department",
            "phone",
            "bio",
            "avatar",
        )

    def validate_avatar(self, value):
        """Validate avatar image size."""
        if value and value.size > 5 * 1024 * 1024:  # 5 MB
            raise serializers.ValidationError("Avatar image must be under 5 MB.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management. Includes all fields."""

    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "department",
            "phone",
            "bio",
            "is_active",
            "is_staff",
            "is_verified",
            "date_joined",
            "last_login",
            "roles",
        )
        read_only_fields = ("id", "date_joined", "last_login")

    def get_roles(self, obj):
        return list(
            obj.userrole_set.select_related("role")
            .values_list("role__name", flat=True)
        )


# =============================================================================
# Role & Permission Serializers
# =============================================================================


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for permissions."""

    class Meta:
        model = Permission
        fields = ("id", "codename", "name", "description")
        read_only_fields = ("id",)


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for roles, including nested permissions."""

    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ("id", "name", "description", "is_active", "permissions", "created_at")
        read_only_fields = ("id", "created_at")

    def get_permissions(self, obj):
        perms = Permission.objects.filter(rolepermission__role=obj)
        return PermissionSerializer(perms, many=True).data


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating / updating roles with permission assignment."""

    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="List of permission IDs to assign to this role.",
    )

    class Meta:
        model = Role
        fields = ("id", "name", "description", "is_active", "permission_ids")
        read_only_fields = ("id",)

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", [])
        role = Role.objects.create(**validated_data)
        for pid in permission_ids:
            RolePermission.objects.create(role=role, permission_id=pid)
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if permission_ids is not None:
            instance.rolepermission_set.all().delete()
            for pid in permission_ids:
                RolePermission.objects.create(role=instance, permission_id=pid)
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for assigning / removing roles from users."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = ("id", "user", "role", "user_email", "role_name", "assigned_by", "created_at")
        read_only_fields = ("id", "assigned_by", "created_at")


# =============================================================================
# Audit Log Serializer
# =============================================================================


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""

    user_email = serializers.CharField(source="user.email", read_only=True, default="")

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "user",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "details",
            "ip_address",
            "user_agent",
            "created_at",
        )
        read_only_fields = fields
