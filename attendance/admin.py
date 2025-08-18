from django.contrib import admin
from django.utils.html import format_html
from .models import AttendanceSession, AttendanceRecord, AbsenceReason


@admin.register(AbsenceReason)
class AbsenceReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'requires_notification', 'is_active']
    list_filter = ['requires_notification', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ['student', 'status', 'absence_reason', 'comment', 'notification_sent']
    readonly_fields = ['notification_sent']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'date', 'taken_by', 'attendance_stats',
        'attendance_percentage', 'is_active'
    ]
    list_filter = ['date', 'group', 'taken_by', 'is_active']
    search_fields = ['group__name', 'taken_by__first_name', 'taken_by__last_name']
    ordering = ['-date']
    inlines = [AttendanceRecordInline]
    
    fieldsets = [
        ('Session Info', {
            'fields': ['group', 'date', 'taken_by', 'lesson']
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def attendance_stats(self, obj):
        return format_html(
            'P: <span style="color: green;">{}</span> | '
            'A: <span style="color: red;">{}</span> | '
            'L: <span style="color: orange;">{}</span>',
            obj.present_count, obj.absent_count, obj.late_count
        )
    attendance_stats.short_description = 'P/A/L'
    
    def attendance_percentage(self, obj):
        percentage = obj.attendance_percentage
        if percentage >= 90:
            color = 'green'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, percentage
        )
    attendance_percentage.short_description = 'Attendance %'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session_info', 'status_display',
        'absence_reason', 'notification_sent'
    ]
    list_filter = ['status', 'absence_reason', 'notification_sent', 'session__date']
    search_fields = [
        'student__first_name', 'student__last_name',
        'session__group__name'
    ]
    ordering = ['-session__date', 'student__first_name']
    
    fieldsets = [
        ('Record Info', {
            'fields': ['session', 'student', 'status']
        }),
        ('Absence Details', {
            'fields': ['absence_reason', 'comment']
        }),
        ('Notification', {
            'fields': ['notification_sent']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    readonly_fields = ['notification_sent']
    
    def session_info(self, obj):
        return f"{obj.session.group.name} - {obj.session.date}"
    session_info.short_description = 'Session'
    
    def status_display(self, obj):
        colors = {
            'present': 'green',
            'late': 'orange',
            'absent_excused': 'blue',
            'absent_unexcused': 'red',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'