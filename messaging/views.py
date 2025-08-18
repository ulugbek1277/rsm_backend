from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import SmsTemplate, SmsLog, Broadcast
from .serializers import (
    SmsTemplateSerializer, SmsLogSerializer,
    BroadcastSerializer, BroadcastCreateSerializer, SendSmsSerializer
)
from .tasks import send_sms, send_broadcast_sms
from apps.core.permissions import IsSuperAdmin, IsAdminOrReadOnly
from apps.core.views import BaseModelViewSet


class SmsTemplateViewSet(BaseModelViewSet):
    """
    ViewSet for SMS Template management
    """
    queryset = SmsTemplate.objects.all()
    serializer_class = SmsTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['name', 'code', 'text']
    ordering_fields = ['name', 'code', 'created_at']
    
    @action(detail=False, methods=['post'])
    def create_defaults(self, request):
        """
        Create default SMS templates
        """
        defaults = SmsTemplate.get_default_templates()
        created_count = 0
        
        for template_data in defaults:
            template, created = SmsTemplate.objects.get_or_create(
                code=template_data['code'],
                defaults=template_data
            )
            if created:
                created_count += 1
        
        return Response({
            'message': f'{created_count} ta default template yaratildi',
            'created_count': created_count
        })
    
    @action(detail=True, methods=['post'])
    def test_render(self, request, pk=None):
        """
        Test template rendering with sample data
        """
        template = self.get_object()
        
        # Sample context data
        sample_context = {
            'parent_name': 'Ahmadjon Karimov',
            'student_name': 'Farrux Karimov',
            'date': '15.12.2024',
            'group_name': 'Python Boshlang\'ich',
            'amount': '500,000',
            'due_date': '20.12.2024',
            'debt_amount': '1,000,000',
            'center_phone': '+998901234567',
            'status': 'bekor qilindi',
            'note': 'Texnik ishlar tufayli'
        }
        
        rendered_text = template.render(sample_context)
        
        return Response({
            'original_text': template.text,
            'rendered_text': rendered_text,
            'sample_context': sample_context
        })


class SmsLogViewSet(BaseModelViewSet):
    """
    ViewSet for SMS Log management
    """
    queryset = SmsLog.objects.all()
    serializer_class = SmsLogSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['status', 'template', 'sent_at']
    search_fields = ['recipient_phone', 'message']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at']
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get SMS statistics
        """
        # Total statistics
        total_sms = self.get_queryset().count()
        
        # Status breakdown
        status_stats = {}
        for status, _ in SmsLog.STATUS_CHOICES:
            count = self.get_queryset().filter(status=status).count()
            status_stats[status] = count
        
        # Daily statistics (last 7 days)
        daily_stats = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = self.get_queryset().filter(created_at__date=date).count()
            daily_stats.append({
                'date': date,
                'count': count
            })
        
        # Success rate
        sent_count = self.get_queryset().filter(status__in=['sent', 'delivered']).count()
        success_rate = 0
        if total_sms > 0:
            success_rate = round((sent_count / total_sms) * 100, 1)
        
        return Response({
            'total_sms': total_sms,
            'status_breakdown': status_stats,
            'success_rate': success_rate,
            'daily_stats': daily_stats
        })
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """
        Get failed SMS logs
        """
        failed_sms = self.get_queryset().filter(status='failed')
        
        page = self.paginate_queryset(failed_sms)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(failed_sms, many=True)
        return Response(serializer.data)


class BroadcastViewSet(BaseModelViewSet):
    """
    ViewSet for Broadcast management
    """
    queryset = Broadcast.objects.all()
    serializer_class = BroadcastSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['audience_type', 'status', 'target_group']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'scheduled_for', 'started_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BroadcastCreateSerializer
        return BroadcastSerializer
    
    @action(detail=True, methods=['post'])
    def start_sending(self, request, pk=None):
        """
        Start sending broadcast
        """
        broadcast = self.get_object()
        
        if broadcast.status != 'draft':
            return Response(
                {'error': 'Faqat qoralama holatidagi broadcast yuborish mumkin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        broadcast.start_sending()
        
        serializer = self.get_serializer(broadcast)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def preview_recipients(self, request, pk=None):
        """
        Preview broadcast recipients
        """
        broadcast = self.get_object()
        recipients = broadcast.get_recipients()
        
        return Response({
            'recipient_count': len(recipients),
            'recipients': recipients[:50],  # Show first 50
            'audience_type': broadcast.get_audience_type_display(),
            'target_group': broadcast.target_group.name if broadcast.target_group else None
        })
    
    @action(detail=False, methods=['post'])
    def send_single_sms(self, request):
        """
        Send single SMS
        """
        serializer = SendSmsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        message = serializer.validated_data['message']
        template_id = serializer.validated_data.get('template_id')
        
        # Queue SMS
        task = send_sms.delay(phone, message, template_id)
        
        return Response({
            'message': 'SMS yuborish navbatga qo\'shildi',
            'task_id': task.id,
            'phone': phone
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent broadcasts
        """
        recent_broadcasts = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_broadcasts, many=True)
        return Response(serializer.data)


# Manual task triggers for testing
class MessagingTasksViewSet(viewsets.ViewSet):
    """
    ViewSet for manually triggering messaging tasks
    """
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['post'])
    def send_payment_reminders(self, request):
        """
        Manually trigger payment reminders
        """
        from .tasks import send_payment_reminders
        task = send_payment_reminders.delay()
        
        return Response({
            'message': 'To\'lov eslatmalari yuborish boshlandi',
            'task_id': task.id
        })
    
    @action(detail=False, methods=['post'])
    def send_debt_notifications(self, request):
        """
        Manually trigger debt notifications
        """
        from .tasks import send_debt_notifications
        task = send_debt_notifications.delay()
        
        return Response({
            'message': 'Qarz haqida xabarlar yuborish boshlandi',
            'task_id': task.id
        })
