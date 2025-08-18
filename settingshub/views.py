from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.http import JsonResponse

from apps.core.permissions import IsSuperAdminOrAdministrator
from .models import GlobalSettings, UserSettings, SettingsCategory, SettingsBackup
from .serializers import (
    GlobalSettingsSerializer, UserSettingsSerializer, 
    SettingsCategorySerializer, SettingsBackupSerializer,
    SettingsExportSerializer, SettingsImportSerializer
)


class GlobalSettingsViewSet(viewsets.ModelViewSet):
    queryset = GlobalSettings.objects.all()
    serializer_class = GlobalSettingsSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrAdministrator]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'setting_type', 'is_active', 'is_public']
    search_fields = ['key', 'description']
    ordering = ['category', 'key']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get settings grouped by category"""
        categories = SettingsCategory.objects.filter(is_active=True)
        result = {}
        
        for category in categories:
            settings = GlobalSettings.objects.filter(
                category=category.name, 
                is_active=True
            )
            result[category.name] = {
                'category_info': SettingsCategorySerializer(category).data,
                'settings': GlobalSettingsSerializer(settings, many=True).data
            }
        
        return Response(result)

    @action(detail=False, methods=['get'])
    def public_settings(self, request):
        """Get public settings for frontend"""
        settings = GlobalSettings.get_all_settings(public_only=True)
        return Response(settings)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update settings"""
        settings_data = request.data.get('settings', [])
        updated_settings = []
        
        for setting_data in settings_data:
            key = setting_data.get('key')
            if key:
                try:
                    setting = GlobalSettings.objects.get(key=key)
                    serializer = GlobalSettingsSerializer(
                        setting, 
                        data=setting_data, 
                        partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()
                        updated_settings.append(serializer.data)
                except GlobalSettings.DoesNotExist:
                    pass
        
        # Clear cache
        cache.clear()
        
        return Response({
            'updated_count': len(updated_settings),
            'updated_settings': updated_settings
        })

    @action(detail=False, methods=['post'])
    def export_settings(self, request):
        """Export settings"""
        serializer = SettingsExportSerializer(data=request.data)
        if serializer.is_valid():
            categories = serializer.validated_data.get('categories', [])
            include_inactive = serializer.validated_data.get('include_inactive', False)
            
            queryset = GlobalSettings.objects.all()
            if categories:
                queryset = queryset.filter(category__in=categories)
            if not include_inactive:
                queryset = queryset.filter(is_active=True)
            
            settings_data = {}
            for setting in queryset:
                settings_data[setting.key] = {
                    'value': setting.value,
                    'setting_type': setting.setting_type,
                    'description': setting.description,
                    'category': setting.category,
                    'is_active': setting.is_active,
                    'is_public': setting.is_public,
                }
            
            return Response({
                'settings_data': settings_data,
                'export_count': len(settings_data)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def import_settings(self, request):
        """Import settings"""
        serializer = SettingsImportSerializer(data=request.data)
        if serializer.is_valid():
            settings_data = serializer.validated_data['settings_data']
            overwrite_existing = serializer.validated_data.get('overwrite_existing', False)
            
            created_count = 0
            updated_count = 0
            
            for key, data in settings_data.items():
                setting, created = GlobalSettings.objects.get_or_create(
                    key=key,
                    defaults={
                        'value': data['value'],
                        'setting_type': data.get('setting_type', 'string'),
                        'description': data.get('description', ''),
                        'category': data.get('category', 'general'),
                        'is_active': data.get('is_active', True),
                        'is_public': data.get('is_public', False),
                    }
                )
                
                if created:
                    created_count += 1
                elif overwrite_existing:
                    setting.value = data['value']
                    setting.setting_type = data.get('setting_type', setting.setting_type)
                    setting.description = data.get('description', setting.description)
                    setting.category = data.get('category', setting.category)
                    setting.is_active = data.get('is_active', setting.is_active)
                    setting.is_public = data.get('is_public', setting.is_public)
                    setting.save()
                    updated_count += 1
            
            # Clear cache
            cache.clear()
            
            return Response({
                'created_count': created_count,
                'updated_count': updated_count,
                'total_processed': len(settings_data)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSettingsViewSet(viewsets.ModelViewSet):
    queryset = UserSettings.objects.all()
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user', 'setting_type']
    search_fields = ['key']

    def get_queryset(self):
        # Users can only see their own settings unless they're admin
        if self.request.user.is_staff:
            return UserSettings.objects.all()
        return UserSettings.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """Get current user's settings"""
        settings = UserSettings.objects.filter(user=request.user)
        serializer = UserSettingsSerializer(settings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_setting(self, request):
        """Set a user setting"""
        key = request.data.get('key')
        value = request.data.get('value')
        setting_type = request.data.get('setting_type', 'string')
        
        if not key or value is None:
            return Response(
                {'error': 'key va value majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        setting = UserSettings.set_user_setting(
            request.user, key, value, setting_type
        )
        serializer = UserSettingsSerializer(setting)
        return Response(serializer.data)


class SettingsCategoryViewSet(viewsets.ModelViewSet):
    queryset = SettingsCategory.objects.all()
    serializer_class = SettingsCategorySerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrAdministrator]
    ordering = ['order', 'name']


class SettingsBackupViewSet(viewsets.ModelViewSet):
    queryset = SettingsBackup.objects.all()
    serializer_class = SettingsBackupSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrAdministrator]
    ordering = ['-created_at']

    def perform_create(self, serializer):
        # Create backup with current settings
        name = serializer.validated_data['name']
        description = serializer.validated_data.get('description', '')
        
        backup = SettingsBackup.create_backup(
            name=name,
            description=description,
            user=self.request.user
        )
        
        return Response(SettingsBackupSerializer(backup).data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore settings from backup"""
        backup = self.get_object()
        backup.restore_settings()
        
        return Response({
            'message': 'Sozlamalar muvaffaqiyatli tiklandi',
            'restored_count': len(backup.settings_data)
        })
