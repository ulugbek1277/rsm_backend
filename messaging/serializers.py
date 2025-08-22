from rest_framework import serializers
from .models import SmsTemplate, SmsLog, Broadcast
from core.serializers import BaseModelSerializer


class SmsTemplateSerializer(BaseModelSerializer):
    """
    SMS template serializer
    """
    class Meta:
        model = SmsTemplate
        fields = [
            'id', 'code', 'name', 'text', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class SmsLogSerializer(BaseModelSerializer):
    """
    SMS log serializer
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = SmsLog
        fields = [
            'id', 'recipient_phone', 'message', 'status', 'status_display',
            'provider_id', 'sent_at', 'delivered_at', 'error_message',
            'template', 'template_name', 'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class BroadcastSerializer(BaseModelSerializer):
    """
    Broadcast serializer
    """
    audience_type_display = serializers.CharField(source='get_audience_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_group_name = serializers.CharField(source='target_group.name', read_only=True)
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Broadcast
        fields = [
            'id', 'title', 'content', 'audience_type', 'audience_type_display',
            'target_group', 'target_group_name', 'custom_phones',
            'scheduled_for', 'status', 'status_display', 'total_recipients',
            'sent_count', 'failed_count', 'success_rate', 'started_at',
            'completed_at', 'is_active', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'total_recipients', 'sent_count', 'failed_count', 'success_rate',
            'started_at', 'completed_at'
        )


class BroadcastCreateSerializer(serializers.ModelSerializer):
    """
    Broadcast creation serializer
    """
    class Meta:
        model = Broadcast
        fields = [
            'title', 'content', 'audience_type', 'target_group',
            'custom_phones', 'scheduled_for'
        ]
    
    def validate(self, attrs):
        """
        Validate broadcast creation
        """
        audience_type = attrs['audience_type']
        target_group = attrs.get('target_group')
        custom_phones = attrs.get('custom_phones', '')
        
        if audience_type in ['group_students', 'group_parents'] and not target_group:
            raise serializers.ValidationError(
                "Guruh tanlangan audience uchun target_group kerak"
            )
        
        if audience_type == 'custom' and not custom_phones.strip():
            raise serializers.ValidationError(
                "Maxsus audience uchun telefon raqamlar kerak"
            )
        
        return attrs


class SendSmsSerializer(serializers.Serializer):
    """
    Serializer for sending single SMS
    """
    phone = serializers.CharField(max_length=13)
    message = serializers.CharField(max_length=1000)
    template_id = serializers.IntegerField(required=False)
    
    def validate_phone(self, value):
        """
        Validate phone number format
        """
        import re
        if not re.match(r'^\+998[0-9]{9}$', value):
            raise serializers.ValidationError("Telefon raqam formati: +998XXXXXXXXX")
        return value
