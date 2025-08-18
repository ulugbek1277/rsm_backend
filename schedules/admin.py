from django.contrib import admin
from django.utils.html import format_html
from .models import Lesson, CalendarOverride


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'room', 'weekday_display', 'time_slot',
        'duration_hours', 'is_active'
    ]
    list_filter = ['weekday', 'room', 'group__course', 'is_active']
    search_fields = ['group__name', 'room__name']
    ordering = ['weekday', 'start_time']
    
    fieldsets = [
        ('Schedule Info', {
            'fields': ['group', 'room', 'weekday']
        }),
        ('Time', {
            'fields': [('start_time', 'end_time')]
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def weekday_display(self, obj):
        return obj.get_weekday_display()
    weekday_display.short_description = 'Weekday'
    
    def time_slot(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    time_slot.short_description = 'Time'
    
    def duration_hours(self, obj):
        return f"{obj.duration_hours:.1f}h"
    duration_hours.short_description = 'Duration'


@admin.register(CalendarOverride)
class CalendarOverrideAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'group', 'room', 'status_display',
        'notification_sent', 'is_active'
    ]
    list_filter = ['is_canceled', 'notification_sent', 'date', 'group']
    search_fields = ['group__name', 'room__name', 'note']
    ordering = ['-date']
    
    fieldsets = [
        ('Override Info', {
            'fields': ['date', 'group', 'room']
        }),
        ('Changes', {
            'fields': [
                'is_canceled',
                ('alternative_time', 'alternative_room'),
                'note'
            ]
        }),
        ('Notification', {
            'fields': [('notify_students', 'notification_sent')]
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    readonly_fields = ['notification_sent']
    
    def status_display(self, obj):
        if obj.is_canceled:
            return format_html(
                '<span style="color: red; font-weight: bold;">Bekor qilingan</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">O\'zgartirilgan</span>'
            )
    status_display.short_description = 'Status'
