from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission for SuperAdmin role only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.SUPER_ADMIN
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission for Admin with full access, others read-only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR]:
            return True
        
        return request.method in permissions.SAFE_METHODS


class IsTeacherOfGroup(permissions.BasePermission):
    """
    Permission for teachers to access only their groups
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR, User.TEACHER]
        )
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR]:
            return True
        
        if request.user.role == User.TEACHER:
            # Check if teacher is assigned to this group
            if hasattr(obj, 'teacher'):
                return obj.teacher == request.user
            elif hasattr(obj, 'group'):
                return obj.group.teacher == request.user
        
        return False


class IsAccountant(permissions.BasePermission):
    """
    Permission for Accountant role
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR, User.ACCOUNTANT]
        )


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Permission for users to access their own data or admins
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR]:
            return True
        
        # Check if accessing own data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user
        
        return obj == request.user

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Agar foydalanuvchi staff bo'lsa, barcha CRUD amallar ruxsat etiladi,
    aks holda faqat o'qish (GET, HEAD, OPTIONS) ruxsat etiladi.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsGroupMember(permissions.BasePermission):
    """
    Permission for group members (students and teachers)
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in [User.SUPER_ADMIN, User.ADMINISTRATOR]:
            return True
        
        if request.user.role == User.TEACHER:
            if hasattr(obj, 'teacher'):
                return obj.teacher == request.user
            elif hasattr(obj, 'group'):
                return obj.group.teacher == request.user
        
        if request.user.role == User.STUDENT:
            if hasattr(obj, 'group'):
                return obj.group.students.filter(user=request.user).exists()
        
        return False