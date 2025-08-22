from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, EmployeeProfile, StudentProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    EmployeeProfileSerializer,
    StudentProfileSerializer
)
from core.permissions import IsSuperAdmin, IsAdminOrReadOnly, IsSelfOrAdmin
from core.views import BaseModelViewSet


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT login view
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(BaseModelViewSet):
    """
    ViewSet for User management
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'phone', 'email']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [IsSuperAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrReadOnly]
        elif self.action in ['retrieve', 'profile', 'update_profile']:
            permission_classes = [IsSelfOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'update_profile':
            return ProfileUpdateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Get current user profile
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update current user profile
        """
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change user password
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Parol muvaffaqiyatli o\'zgartirildi'})
    
    @action(detail=False, methods=['get'])
    def staff(self, request):
        """
        Get all staff members
        """
        staff_users = self.get_queryset().filter(
            role__in=[User.SUPER_ADMIN, User.ADMINISTRATOR, User.TEACHER, User.ACCOUNTANT]
        )
        page = self.paginate_queryset(staff_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        """
        Get all students
        """
        students = self.get_queryset().filter(role=User.STUDENT)
        page = self.paginate_queryset(students)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def teachers(self, request):
        """
        Get all teachers
        """
        teachers = self.get_queryset().filter(role=User.TEACHER)
        page = self.paginate_queryset(teachers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(teachers, many=True)
        return Response(serializer.data)


class EmployeeProfileViewSet(BaseModelViewSet):
    """
    ViewSet for Employee Profile management
    """
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['position', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'position']
    ordering_fields = ['user__first_name', 'hire_date']


class StudentProfileViewSet(BaseModelViewSet):
    """
    ViewSet for Student Profile management
    """
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['school_grade', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'parent_name', 'school_name']
    ordering_fields = ['user__first_name', 'birth_date']