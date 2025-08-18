from django.contrib import admin
from .models import SystemSettings, NotificationSettings, PaymentSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'is_active', 'updated_at']
    list_filter = ['setting_type', 'is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('key', 'value', 'setting_type', 'is_active')
        }),
        ('Qo\'shimcha', {
            'fields': ('description',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['sms_enabled', 'sms_absence_enabled', 'sms_payment_reminder', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('SMS sozlamalari', {
            'fields': ('sms_enabled', 'sms_absence_enabled', 'sms_payment_reminder', 'sms_debt_warning')
        }),
        ('SMS shablonlari', {
            'fields': ('absence_sms_template', 'payment_reminder_template', 'debt_warning_template')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ['default_currency', 'payment_due_days', 'late_payment_fee', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Asosiy sozlamalar', {
            'fields': ('default_currency', 'payment_due_days', 'late_payment_fee', 'debt_warning_days')
        }),
        ('Chegirma sozlamalari', {
            'fields': ('sibling_discount', 'early_payment_discount')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
