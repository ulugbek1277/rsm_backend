from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Group, GroupStudent
from .serializers import (
    GroupSerializer, GroupCreateSerializer, GroupListSerializer,
    GroupStudentSerializer, GroupStudentCreateSerializer
)
from apps.core.permissions import IsAdminOrReadOnly, IsTeacherOfGroup
from apps.core.views import BaseModelViewSet


class GroupViewSet(BaseModelViewSet):
    """
    ViewSet for Group management
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['course', 'teacher', 'status', 'room']
    search_fields = ['name', 'course__title', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['name', 'planned_start', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GroupCreateSerializer
        elif self.action == 'list':
            return GroupListSerializer
        return GroupSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active groups
        """
        active_groups = self.get_queryset().filter(status='active')
        page = self.paginate_queryset(active_groups)
        if page is not None:
            serializer = GroupListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GroupListSerializer(active_groups, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """
        Get groups for current teacher
        """
        if request.user.role != request.user.TEACHER:
            return Response(
                {'error': 'Faqat o\'qituvchilar uchun'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        my_groups = self.get_queryset().filter(teacher=request.user)
        page = self.paginate_queryset(my_groups)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(my_groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start group (change status to active)
        """
        group = self.get_object()
        group.status = 'active'
        group.actual_start = timezone.now().date()
        group.save()
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete group
        """
        group = self.get_object()
        group.status = 'completed'
        group.actual_end = timezone.now().date()
        group.save()
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive group and deactivate all students
        """
        group = self.get_object()
        group.status = 'archived'
        group.save()
        
        # Deactivate all group students
        GroupStudent.objects.filter(group=group, is_active=True).update(
            is_active=False,
            left_at=timezone.now().date()
        )
        
        serializer = self.get_serializer(group)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'])
    def students(self, request, pk=None):
        """
        Get or add students to group
        """
        group = self.get_object()
        
        if request.method == 'GET':
            students = group.students.filter(is_active=True)
            page = self.paginate_queryset(students)
            if page is not None:
                serializer = GroupStudentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = GroupStudentSerializer(students, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data['group'] = group.id
            
            serializer = GroupStudentCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupStudentViewSet(BaseModelViewSet):
    """
    ViewSet for Group Student management
    """
    queryset = GroupStudent.objects.all()
    serializer_class = GroupStudentSerializer
    permission_classes = [IsTeacherOfGroup]
    filterset_fields = ['group', 'student', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'group__name']
    ordering_fields = ['joined_at', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GroupStudentCreateSerializer
        return GroupStudentSerializer
    
    @action(detail=True, methods=['post'])
    def remove_from_group(self, request, pk=None):
        """
        Remove student from group
        """
        group_student = self.get_object()
        group_student.is_active = False
        group_student.left_at = timezone.now().date()
        group_student.save()
        
        serializer = self.get_serializer(group_student)
        return Response(serializer.data)
