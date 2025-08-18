from django.contrib import admin
from django.utils.html import format_html
from .models import Group, GroupStudent


class GroupStudentInline(admin.TabularInline):
    model = GroupStudent
    extra = 0
    fields = ['student', 'joined_at', 'left_at', 'is_active']
    readonly_fields = ['joined_at']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'course', 'teacher', 'status', 'current_students_count',
        'max_students', 'completion_percentage', 'planned_start', 'is_active'
    ]
    list_filter = ['status', 'course', 'teacher', 'planned_start', 'is_active']
    search_fields = ['name', 'course__title', 'teacher__first_name', 'teacher__last_name']
    ordering = ['-created_at']
    inlines = [GroupStudentInline]
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['name', 'course', 'teacher', 'room']
        }),
        ('Dates', {
            'fields': [
                ('planned_start', 'planned_end'),
                ('actual_start', 'actual_end')
            ]
        }),
        ('Settings', {
            'fields': ['max_students', 'status', 'description']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def current_students_count(self, obj):
        count = obj.current_students_count
        max_count = obj.max_students
        
        if count >= max_count:
            color = 'red'
        elif count >= max_count * 0.8:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{}</span>',
            color, count, max_count
        )
    current_students_count.short_description = 'Students'
    
    def completion_percentage(self, obj):
        percentage = obj.completion_percentage
        if percentage >= 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'gray'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, percentage
        )
    completion_percentage.short_description = 'Progress'


@admin.register(GroupStudent)
class GroupStudentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'group', 'joined_at', 'left_at',
        'is_currently_active', 'duration_days'
    ]
    list_filter = ['group', 'joined_at', 'is_active']
    search_fields = [
        'student__first_name', 'student__last_name',
        'group__name'
    ]
    ordering = ['-joined_at']
    
    fieldsets = [
        ('Assignment', {
            'fields': ['group', 'student']
        }),
        ('Dates', {
            'fields': [('joined_at', 'left_at')]
        }),
        ('Notes', {
            'fields': ['notes']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def is_currently_active(self, obj):
        if obj.is_currently_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓</span>'
            )
        return format_html(
            '<span style="color: red;">✗</span>'
        )
    is_currently_active.short_description = 'Active'
