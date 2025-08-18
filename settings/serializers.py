from rest_framework import serializers
from .models import SystemSettings, NotificationSettings, PaymentSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'typed_value', 'setting_type', 'description', 'is_active']

    def get_typed_value(self, obj):
        return obj.get_typed_value()


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'sms_enabled', 'sms_absence_enabled', 'sms_payment_reminder',
            'sms_debt_warning', 'absence_sms_template', 'payment_reminder_template',
            'debt_warning_template', 'created_at', 'updated_at'
        ]


class PaymentSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSettings
        fields = [
            'id', 'default_currency', 'late_payment_fee', 'payment_due_days',
            'debt_warning_days', 'sibling_discount', 'early_payment_discount',
            'created_at', 'updated_at'
        ]
