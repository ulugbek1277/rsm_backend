from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from core.permissions import IsStaffOrReadOnly
from .models import Student, StudentEnrollment, StudentDocument, StudentNote
from .serializers import (
    StudentSerializer, StudentListSerializer, StudentDetailSerializer,
    StudentEnrollmentSerializer, StudentDocumentSerializer, StudentNoteSerializer
)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'gender', 'education_level', 'region']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'enrollment_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        elif self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer

    def get_queryset(self):
        queryset = Student.objects.select_related('user').prefetch_related(
            'enrollments__course', 'documents', 'notes'
        )
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by debt
        has_debt = self.request.query_params.get('has_debt')
        if has_debt == 'true':
            queryset = queryset.filter(total_debt__gt=0)
        elif has_debt == 'false':
            queryset = queryset.filter(total_debt=0)
        
        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status='active').count()
        students_with_debt = Student.objects.filter(total_debt__gt=0).count()
        total_debt = Student.objects.aggregate(Sum('total_debt'))['total_debt__sum'] or 0
        
        # New students this month
        current_month = timezone.now().replace(day=1)
        new_students_this_month = Student.objects.filter(
            enrollment_date__gte=current_month
        ).count()

        return Response({
            'total_students': total_students,
            'active_students': active_students,
            'inactive_students': total_students - active_students,
            'students_with_debt': students_with_debt,
            'total_debt': total_debt,
            'new_students_this_month': new_students_this_month,
        })

    @action(detail=True, methods=['post'])
    def enroll_course(self, request, pk=None):
        """Enroll student in a course"""
        student = self.get_object()
        course_id = request.data.get('course_id')
        start_date = request.data.get('start_date', timezone.now().date())

        if not course_id:
            return Response(
                {'error': 'course_id majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already enrolled
        if StudentEnrollment.objects.filter(
            student=student, course_id=course_id, status='active'
        ).exists():
            return Response(
                {'error': 'Talaba bu kursga allaqachon ro\'yxatdan o\'tgan'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment_data = {
            'student': student.id,
            'course_id': course_id,
            'start_date': start_date
        }
        
        serializer = StudentEnrollmentSerializer(data=enrollment_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get student payment history"""
        student = self.get_object()
        from apps.payments.models import Payment
        from apps.payments.serializers import PaymentSerializer
        
        payments = Payment.objects.filter(student=student).order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendance_report(self, request, pk=None):
        """Get student attendance report"""
        student = self.get_object()
        from apps.attendance.models import AttendanceRecord
        
        # Get attendance for last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        attendance_records = AttendanceRecord.objects.filter(
            student=student,
            session__date__gte=thirty_days_ago
        ).select_related('session')
        
        total_sessions = attendance_records.count()
        present_sessions = attendance_records.filter(status='present').count()
        attendance_percentage = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0

        return Response({
            'total_sessions': total_sessions,
            'present_sessions': present_sessions,
            'absent_sessions': total_sessions - present_sessions,
            'attendance_percentage': round(attendance_percentage, 2),
            'period': '30 days'
        })


class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.all()
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'course', 'student']
    search_fields = ['student__first_name', 'student__last_name', 'course__title']

    def get_queryset(self):
        return StudentEnrollment.objects.select_related(
            'student', 'course'
        ).order_by('-enrollment_date')


class StudentDocumentViewSet(viewsets.ModelViewSet):
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['document_type', 'student']

    def get_queryset(self):
        return StudentDocument.objects.select_related('student').order_by('-created_at')


class StudentNoteViewSet(viewsets.ModelViewSet):
    queryset = StudentNote.objects.all()
    serializer_class = StudentNoteSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['note_type', 'student', 'is_important']
    search_fields = ['title', 'content']

    def get_queryset(self):
        return StudentNote.objects.select_related(
            'student', 'author'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
