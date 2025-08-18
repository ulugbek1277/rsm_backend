from django.contrib import admin
from django.utils.html import format_html
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'price_monthly', 'duration_months',
        'max_students', 'active_groups_count', 'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'duration_months', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['title']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ['title', 'slug', 'description']
        }),
        ('Pricing & Duration', {
            'fields': [
                ('price_monthly', 'duration_months'),
                'max_students'
            ]
        }),
        ('Course Details', {
            'fields': ['prerequisites', 'objectives', 'syllabus']
        }),
        ('Certificate', {
            'fields': ['certificate_template']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    readonly_fields = ['active_groups_count']
    
    def active_groups_count(self, obj):
        count = obj.active_groups_count
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return count
    active_groups_count.short_description = 'Active Groups'
