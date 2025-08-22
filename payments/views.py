from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import timedelta

from .models import Invoice, Payment, DebtSnapshot
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceListSerializer,
    PaymentSerializer, PaymentCreateSerializer,
    DebtSnapshotSerializer, DebtorReportSerializer
)
from core.permissions import IsAccountant, IsAdminOrReadOnly
from core.views import BaseModelViewSet
from accounts.models import User


class InvoiceViewSet(BaseModelViewSet):
    """
    ViewSet for Invoice management
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAccountant]
    filterset_fields = ['student', 'group', 'status', 'due_date']
    search_fields = ['student__first_name', 'student__last_name', 'description']
    ordering_fields = ['issued_at', 'due_date', 'amount', 'remaining_amount']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        elif self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending invoices
        """
        pending_invoices = self.get_queryset().filter(
            status__in=['pending', 'partial'],
            is_active=True
        )
        
        page = self.paginate_queryset(pending_invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = InvoiceListSerializer(pending_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get overdue invoices
        """
        today = timezone.now().date()
        overdue_invoices = self.get_queryset().filter(
            due_date__lt=today,
            status__in=['pending', 'partial', 'overdue'],
            is_active=True
        )
        
        page = self.paginate_queryset(overdue_invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = InvoiceListSerializer(overdue_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def debtors(self, request):
        """
        Get list of students with debt
        """
        # Get students with unpaid invoices
        debtors_data = []
        
        students_with_debt = User.objects.filter(
            role=User.STUDENT,
            invoices__status__in=['pending', 'partial', 'overdue'],
            invoices__is_active=True
        ).distinct()
        
        for student in students_with_debt:
            unpaid_invoices = student.invoices.filter(
                status__in=['pending', 'partial', 'overdue'],
                is_active=True
            )
            
            total_debt = Decimal('0.00')
            overdue_debt = Decimal('0.00')
            max_overdue_days = 0
            
            for invoice in unpaid_invoices:
                remaining = invoice.remaining_amount
                total_debt += remaining
                
                if invoice.is_overdue:
                    overdue_debt += remaining
                    max_overdue_days = max(max_overdue_days, invoice.days_overdue)
            
            parent_phone = ''
            if hasattr(student, 'student_profile'):
                parent_phone = student.student_profile.parent_phone
            
            debtors_data.append({
                'student_id': student.id,
                'student_name': student.get_full_name(),
                'student_phone': student.phone,
                'parent_phone': parent_phone,
                'total_debt': total_debt,
                'overdue_debt': overdue_debt,
                'overdue_days': max_overdue_days,
                'invoice_count': unpaid_invoices.count()
            })
        
        # Sort by total debt descending
        debtors_data.sort(key=lambda x: x['total_debt'], reverse=True)
        
        serializer = DebtorReportSerializer(debtors_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get payment statistics
        """
        today = timezone.now().date()
        
        # Total statistics
        total_invoices = self.get_queryset().filter(is_active=True).count()
        total_amount = self.get_queryset().filter(is_active=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Status breakdown
        status_stats = {}
        for status, _ in Invoice.STATUS_CHOICES:
            count = self.get_queryset().filter(status=status, is_active=True).count()
            status_stats[status] = count
        
        # Overdue statistics
        overdue_count = self.get_queryset().filter(
            due_date__lt=today,
            status__in=['pending', 'partial', 'overdue'],
            is_active=True
        ).count()
        
        # Monthly statistics
        current_month = today.replace(day=1)
        monthly_invoices = self.get_queryset().filter(
            issued_at__gte=current_month,
            is_active=True
        ).count()
        
        monthly_amount = self.get_queryset().filter(
            issued_at__gte=current_month,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'status_breakdown': status_stats,
            'overdue_count': overdue_count,
            'monthly_invoices': monthly_invoices,
            'monthly_amount': monthly_amount
        })
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """
        Add payment to invoice
        """
        invoice = self.get_object()
        
        data = request.data.copy()
        data['invoice'] = invoice.id
        
        serializer = PaymentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(created_by=request.user)
        
        # Return updated invoice
        invoice_serializer = self.get_serializer(invoice)
        return Response(invoice_serializer.data)


class PaymentViewSet(BaseModelViewSet):
    """
    ViewSet for Payment management
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAccountant]
    filterset_fields = ['invoice', 'method', 'paid_at']
    search_fields = ['invoice__student__first_name', 'invoice__student__last_name', 'note']
    ordering_fields = ['paid_at', 'paid_amount', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's payments
        """
        today = timezone.now().date()
        today_payments = self.get_queryset().filter(
            paid_at__date=today,
            is_active=True
        )
        
        page = self.paginate_queryset(today_payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(today_payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """
        Get monthly payment report
        """
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        monthly_payments = self.get_queryset().filter(
            paid_at__gte=current_month,
            is_active=True
        )
        
        # Statistics
        total_amount = monthly_payments.aggregate(
            total=Sum('paid_amount')
        )['total'] or Decimal('0.00')
        
        total_count = monthly_payments.count()
        
        # Method breakdown
        method_stats = {}
        for method, _ in Payment.METHOD_CHOICES:
            amount = monthly_payments.filter(method=method).aggregate(
                total=Sum('paid_amount')
            )['total'] or Decimal('0.00')
            count = monthly_payments.filter(method=method).count()
            method_stats[method] = {
                'amount': amount,
                'count': count
            }
        
        return Response({
            'month': current_month.strftime('%Y-%m'),
            'total_amount': total_amount,
            'total_count': total_count,
            'method_breakdown': method_stats
        })


class DebtSnapshotViewSet(BaseModelViewSet):
    """
    ViewSet for Debt Snapshot management
    """
    queryset = DebtSnapshot.objects.all()
    serializer_class = DebtSnapshotSerializer
    permission_classes = [IsAccountant]
    filterset_fields = ['snapshot_date', 'student']
    search_fields = ['student__first_name', 'student__last_name']
    ordering_fields = ['snapshot_date', 'total_debt', 'overdue_days']
    
    @action(detail=False, methods=['post'])
    def create_daily_snapshot(self, request):
        """
        Create debt snapshots for all students
        """
        date_str = request.data.get('date')
        if date_str:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        snapshots = DebtSnapshot.create_daily_snapshots(date)
        
        return Response({
            'message': f'{len(snapshots)} ta snapshot yaratildi',
            'date': date,
            'count': len(snapshots)
        })
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest debt snapshots
        """
        latest_date = self.get_queryset().aggregate(
            latest=models.Max('snapshot_date')
        )['latest']
        
        if not latest_date:
            return Response([])
        
        latest_snapshots = self.get_queryset().filter(
            snapshot_date=latest_date
        ).order_by('-total_debt')
        
        page = self.paginate_queryset(latest_snapshots)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(latest_snapshots, many=True)
        return Response(serializer.data)
