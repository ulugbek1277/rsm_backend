from django.contrib import admin
from django.utils.html import format_html
from .models import SmsTemplate, SmsLog, Broadcast


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'text']
    ordering = ['name']
    
    fieldsets = [
        ('Template Info', {
            'fields': ['code', 'name', 'description']
        }),
        ('Content', {
            'fields': ['text']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_phone', 'status_display', 'template',
        'sent_at', 'delivered_at', 'created_at'
    ]
    list_filter = ['status', 'template', 'sent_at', 'created_at']
    search_fields = ['recipient_phone', 'message', 'error_message']
    ordering = ['-created_at']
    
    fieldsets = [
        ('SMS Info', {
            'fields': ['recipient_phone', 'message', 'template']
        }),
        ('Status', {
            'fields': ['status', 'provider_id']
        }),
        ('Timestamps', {
            'fields': ['sent_at', 'delivered_at']
        }),
        ('Error Info', {
            'fields': ['error_message']
        })
    ]
    
    readonly_fields = ['sent_at', 'delivered_at']
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'sent': 'blue',
            'delivered': 'green',
            'failed': 'red',
            'rejected': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'audience_type_display', 'status_display',
        'total_recipients', 'success_rate', 'scheduled_for'
    ]
    list_filter = ['audience_type', 'status', 'scheduled_for', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']
    
    fieldsets = [
        ('Broadcast Info', {
            'fields': ['title', 'content']
        }),
        ('Audience', {
            'fields': [
                'audience_type', 'target_group', 'custom_phones'
            ]
        }),
        ('Scheduling', {
            'fields': ['scheduled_for']
        }),
        ('Statistics', {
            'fields': [
                ('total_recipients', 'sent_count', 'failed_count'),
                ('started_at', 'completed_at')
            ]
        }),
        ('Status', {
            'fields': ['status', 'is_active']
        })
    ]
    
    readonly_fields = [
        'total_recipients', 'sent_count', 'failed_count',
        'started_at', 'completed_at'
    ]
    
    def audience_type_display(self, obj):
        return obj.get_audience_type_display()
    audience_type_display.short_description = 'Audience'
    
    def status_display(self, obj):
        colors = {
            'draft': 'gray',
            'scheduled': 'orange',
            'sending': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def success_rate(self, obj):
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, rate
        )
    success_rate.short_description = 'Success Rate'
