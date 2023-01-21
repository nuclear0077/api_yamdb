from rest_framework import permissions
from api.utils import is_admin_or_superuser, is_auth


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_auth(request) and is_admin_or_superuser(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_auth(request) and is_admin_or_superuser(request.user)


class IsAuthorAndStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated or
            request.method in permissions.SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_moderator
            or request.user.is_admin
        )
