from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsAdminOrCoordinator(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.ADMIN,
            UserRole.FACULTY_COORDINATOR,
            UserRole.STUDENT_COORDINATOR,
        ]


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == UserRole.STUDENT
