from rest_framework import serializers
from .models import Invoice, Payment, DebtSnapshot
from apps.core.serializers import BaseModelSerializer, UserBasicSerializer


class PaymentSerializer(BaseModelSerializer):
    """
    Payment serializer
    """
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'paid_amount', 'paid_at', 'method',
            'method_display', 'note', 'receipt_number', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Payment creation serializer
    """
    class Meta:
        model = Payment
        fields = ['invoice', 'paid_amount', 'method', 'note', 'receipt_number']
    
    def validate_paid_amount(self, value):
        """
        Validate payment amount
        """
        if value <= 0:
            raise serializers.ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak")
        return value
    
    def validate(self, attrs):
        """
        Validate payment
        """
        invoice = attrs['invoice']
        paid_amount = attrs['paid_amount']
        
        remaining = invoice.remaining_amount
        if paid_amount > remaining:
            raise serializers.ValidationError(
                f"To'lov miqdori qolgan miqdordan ({remaining} so'm) oshmasligi kerak"
            )
        
        return attrs


class InvoiceSerializer(BaseModelSerializer):
    """
    Invoice serializer
    """
    student_info = UserBasicSerializer(source='student', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    final_amount = serializers.ReadOnlyField()
    paid_amount = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'student', 'student_info', 'group', 'group_name',
            'amount', 'discount_amount', 'final_amount', 'due_date',
            'status', 'status_display', 'issued_at', 'description',
            'paid_amount', 'remaining_amount', 'is_overdue', 'days_overdue',
            'payments', 'is_active', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'final_amount', 'paid_amount', 'remaining_amount', 'is_overdue', 'days_overdue'
        )


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """
    Invoice creation serializer
    """
    class Meta:
        model = Invoice
        fields = [
            'student', 'group', 'amount', 'discount_amount',
            'due_date', 'description'
        ]
    
    def validate_amount(self, value):
        """
        Validate invoice amount
        """
        if value <= 0:
            raise serializers.ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak")
        return value
    
    def validate(self, attrs):
        """
        Validate invoice
        """
        amount = attrs['amount']
        discount_amount = attrs.get('discount_amount', 0)
        
        if discount_amount < 0:
            raise serializers.ValidationError("Chegirma miqdori manfiy bo'lishi mumkin emas")
        
        if discount_amount >= amount:
            raise serializers.ValidationError("Chegirma miqdori to'lov miqdoridan kam bo'lishi kerak")
        
        return attrs


class InvoiceListSerializer(serializers.ModelSerializer):
    """
    Simplified invoice serializer for lists
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'student_name', 'group_name', 'amount', 'remaining_amount',
            'due_date', 'status', 'status_display', 'is_overdue', 'issued_at'
        ]


class DebtSnapshotSerializer(BaseModelSerializer):
    """
    Debt snapshot serializer
    """
    student_info = UserBasicSerializer(source='student', read_only=True)
    
    class Meta:
        model = DebtSnapshot
        fields = [
            'id', 'snapshot_date', 'student', 'student_info',
            'total_debt', 'overdue_debt', 'overdue_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class DebtorReportSerializer(serializers.Serializer):
    """
    Serializer for debtor reports
    """
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_phone = serializers.CharField()
    parent_phone = serializers.CharField()
    total_debt = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_debt = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_days = serializers.IntegerField()
    invoice_count = serializers.IntegerField()
