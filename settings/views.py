from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .models import SystemSettings, NotificationSettings, PaymentSettings
from .serializers import (
    SystemSettingsSerializer, 
    NotificationSettingsSerializer, 
    PaymentSettingsSerializer
)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'key'

    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        """Kalit bo'yicha sozlamani olish"""
        key = request.query_params.get('key')
        if not key:
            return Response({'error': 'Kalit talab qilinadi'}, status=status.HTTP_400_BAD_REQUEST)
        
        value = SystemSettings.get_setting(key)
        return Response({'key': key, 'value': value})

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bir nechta sozlamani yangilash"""
        settings_data = request.data.get('settings', [])
        updated_settings = []
        
        for setting_data in settings_data:
            key = setting_data.get('key')
            value = setting_data.get('value')
            
            if key and value is not None:
                setting, created = SystemSettings.objects.update_or_create(
                    key=key,
                    defaults={'value': str(value)}
                )
                updated_settings.append(setting)
        
        serializer = self.get_serializer(updated_settings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """Cache ni tozalash"""
        cache.clear()
        return Response({'message': 'Cache tozalandi'})


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    queryset = NotificationSettings.objects.all()
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Joriy xabarnoma sozlamalari"""
        settings = NotificationSettings.objects.first()
        if not settings:
            settings = NotificationSettings.objects.create()
        
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class PaymentSettingsViewSet(viewsets.ModelViewSet):
    queryset = PaymentSettings.objects.all()
    serializer_class = PaymentSettingsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Joriy to'lov sozlamalari"""
        settings = PaymentSettings.objects.first()
        if not settings:
            settings = PaymentSettings.objects.create()
        
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
