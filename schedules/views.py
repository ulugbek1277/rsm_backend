from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Lesson, CalendarOverride
from .serializers import (
    LessonSerializer, LessonCreateSerializer,
    CalendarOverrideSerializer, CalendarOverrideCreateSerializer
)
from apps.core.permissions import IsAdminOrReadOnly, IsTeacherOfGroup
from apps.core.views import BaseModelViewSet


class LessonViewSet(BaseModelViewSet):
    """
    ViewSet for Lesson management
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsTeacherOfGroup]
    filterset_fields = ['group', 'room', 'weekday', 'is_active']
    search_fields = ['group__name', 'room__name']
    ordering_fields = ['weekday', 'start_time', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LessonCreateSerializer
        return LessonSerializer
    
    @action(detail=False, methods=['get'])
    def weekly_schedule(self, request):
        """
        Get weekly schedule for all groups
        """
        lessons = self.get_queryset().filter(is_active=True).order_by('weekday', 'start_time')
        
        # Group by weekday
        schedule = {}
        for lesson in lessons:
            weekday = lesson.get_weekday_display()
            if weekday not in schedule:
                schedule[weekday] = []
            
            schedule[weekday].append({
                'id': lesson.id,
                'group': lesson.group.name,
                'room': lesson.room.name,
                'time': f"{lesson.start_time} - {lesson.end_time}",
                'duration': lesson.duration_hours
            })
        
        return Response(schedule)
    
    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        """
        Get schedule for current teacher's groups
        """
        if request.user.role != request.user.TEACHER:
            return Response(
                {'error': 'Faqat o\'qituvchilar uchun'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lessons = self.get_queryset().filter(
            group__teacher=request.user,
            is_active=True
        ).order_by('weekday', 'start_time')
        
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's lessons
        """
        today = timezone.now()
        weekday = today.weekday()
        
        lessons = self.get_queryset().filter(
            weekday=weekday,
            is_active=True
        ).order_by('start_time')
        
        serializer = self.get_serializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def next_occurrences(self, request, pk=None):
        """
        Get next 10 occurrences of this lesson
        """
        lesson = self.get_object()
        occurrences = []
        
        current_date = timezone.now().date()
        for i in range(10):
            # Calculate next occurrence
            days_ahead = lesson.weekday - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            occurrence_date = current_date + timedelta(days=days_ahead)
            
            # Check for overrides
            override = CalendarOverride.objects.filter(
                date=occurrence_date,
                group=lesson.group,
                is_active=True
            ).first()
            
            occurrence_info = {
                'date': occurrence_date,
                'time': f"{lesson.start_time} - {lesson.end_time}",
                'room': lesson.room.name,
                'status': 'scheduled'
            }
            
            if override:
                if override.is_canceled:
                    occurrence_info['status'] = 'canceled'
                    occurrence_info['note'] = override.note
                else:
                    occurrence_info['status'] = 'modified'
                    if override.alternative_time:
                        occurrence_info['time'] = f"{override.alternative_time} - {lesson.end_time}"
                    if override.alternative_room:
                        occurrence_info['room'] = override.alternative_room.name
                    occurrence_info['note'] = override.note
            
            occurrences.append(occurrence_info)
            current_date = occurrence_date + timedelta(days=1)
        
        return Response(occurrences)


class CalendarOverrideViewSet(BaseModelViewSet):
    """
    ViewSet for Calendar Override management
    """
    queryset = CalendarOverride.objects.all()
    serializer_class = CalendarOverrideSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['date', 'group', 'room', 'is_canceled']
    search_fields = ['group__name', 'room__name', 'note']
    ordering_fields = ['date', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CalendarOverrideCreateSerializer
        return CalendarOverrideSerializer
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming overrides (next 30 days)
        """
        today = timezone.now().date()
        next_month = today + timedelta(days=30)
        
        overrides = self.get_queryset().filter(
            date__range=[today, next_month],
            is_active=True
        ).order_by('date')
        
        serializer = self.get_serializer(overrides, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's overrides
        """
        today = timezone.now().date()
        overrides = self.get_queryset().filter(date=today, is_active=True)
        
        serializer = self.get_serializer(overrides, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resend_notification(self, request, pk=None):
        """
        Resend notification for this override
        """
        override = self.get_object()
        override.notification_sent = False
        override.save()
        override.send_notification()
        
        return Response({'message': 'Xabar qayta yuborildi'})
