"""
Custom DRF permission classes for the Document Management System.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to admin (staff) users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission that grants access to the owner of the
    object or to admin users.

    The view's queryset model must have an ``owner`` or ``user`` field.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user


class HasRole(BasePermission):
    """
    Checks that the requesting user has one of the required roles.

    Usage in views::

        class MyView(APIView):
            permission_classes = [HasRole]
            required_roles = ['admin', 'editor']
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_roles = getattr(view, "required_roles", [])
        if not required_roles:
            return True

        user_roles = set(
            request.user.userrole_set.values_list("role__name", flat=True)
        )
        return bool(user_roles & set(required_roles))


class HasPermissionCodename(BasePermission):
    """
    Checks that the requesting user has a specific permission codename
    through their assigned roles.

    Usage in views::

        class MyView(APIView):
            permission_classes = [HasPermissionCodename]
            required_permission = 'document.create'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_perm = getattr(view, "required_permission", None)
        if not required_perm:
            return True

        return required_perm in request.user.get_all_permissions_list()


class IsVerified(BasePermission):
    """
    Allows access only to users whose email has been verified.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
        )
