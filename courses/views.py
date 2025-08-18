from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course
from .serializers import CourseSerializer, CourseCreateSerializer, CourseListSerializer
from apps.core.permissions import IsAdminOrReadOnly
from apps.core.views import BaseModelViewSet


class CourseViewSet(BaseModelViewSet):
    """
    ViewSet for Course management
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['is_active', 'duration_months']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price_monthly', 'duration_months', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        elif self.action == 'list':
            return CourseListSerializer
        return CourseSerializer
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular courses (with most active groups)
        """
        from django.db.models import Count
        
        popular_courses = self.get_queryset().annotate(
            groups_count=Count('groups', filter=models.Q(groups__status='active'))
        ).filter(is_active=True).order_by('-groups_count')[:5]
        
        serializer = CourseListSerializer(popular_courses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        """
        Get all groups for this course
        """
        course = self.get_object()
        groups = course.groups.filter(is_active=True)
        
        # Import here to avoid circular import
        from apps.groups.serializers import GroupListSerializer
        serializer = GroupListSerializer(groups, many=True)
        return Response(serializer.data)
