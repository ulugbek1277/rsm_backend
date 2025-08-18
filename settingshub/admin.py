from django.contrib import admin
from .models import GlobalSettings, UserSettings, SettingsCategory, SettingsBackup


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'category', 'is_active', 'is_public']
    list_filter = ['setting_type', 'category', 'is_active', 'is_public']
    search_fields = ['key', 'description']
    list_editable = ['is_active', 'is_public']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('key', 'value', 'setting_type')
        }),
        ('Kategoriya va tavsif', {
            'fields': ('category', 'description')
        }),
        ('Sozlamalar', {
            'fields': ('is_active', 'is_public')
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'value', 'setting_type']
    list_filter = ['setting_type', 'user']
    search_fields = ['user__username', 'key']


@admin.register(SettingsCategory)
class SettingsCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']


@admin.register(SettingsBackup)
class SettingsBackupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['settings_data', 'created_by']
