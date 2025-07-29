from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsNotBlocked(permissions.BasePermission):
    message = "Sizda ushbu amallarni bajarish uchun ruxsat yo'q. Hisobingiz bloklangan. Iltimos, admin bilan bog'laning."

    def has_permission(self, request, view):
        user = request.user
        if getattr(user, 'is_blocked', False):
            raise PermissionDenied(detail=self.message)
        return True