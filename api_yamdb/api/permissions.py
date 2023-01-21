from rest_framework import permissions


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.user)
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
