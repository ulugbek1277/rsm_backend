from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, EmployeeProfile, StudentProfile


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    can_delete = False
    verbose_name_plural = 'Employee Profile'
    fields = [
        'position', 'hire_date', 'salary',
        ('passport_series', 'passport_number'),
        'passport_issued_by', 'passport_issued_date',
        'address', 'birth_date',
        ('emergency_contact_name', 'emergency_contact_phone')
    ]


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fields = [
        ('parent_name', 'parent_phone'),
        'address', 'birth_date', 'avatar',
        ('school_name', 'school_grade'),
        'medical_info', 'notes'
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'get_full_name', 'phone', 'role',
        'is_active', 'date_joined', 'colored_role'
    ]
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'phone', 'email']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'role')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'role', 'first_name', 'last_name', 'email')
        }),
    )

    inlines = []

    def get_inline_instances(self, request, obj=None):
        """Dynamic inlines based on user role"""
        if not obj:
            return []
        inlines = []
        if hasattr(obj, 'role'):
            if obj.role in ['superadmin', 'administrator', 'teacher', 'accountant']:
                inlines.append(EmployeeProfileInline(self.model, self.admin_site))
            elif obj.role == 'student':
                inlines.append(StudentProfileInline(self.model, self.admin_site))
        return inlines

    def colored_role(self, obj):
        colors = {
            'superadmin': '#dc3545',  # Red
            'administrator': '#fd7e14',  # Orange
            'teacher': '#198754',  # Green
            'accountant': '#0d6efd',  # Blue
            'student': '#6f42c1',  # Purple
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    colored_role.short_description = 'Role'


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'position', 'hire_date', 'salary', 'is_active'
    ]
    list_filter = ['position', 'hire_date', 'is_active']
    search_fields = [
        'user__first_name', 'user__last_name',
        'user__username', 'position'
    ]
    ordering = ['-hire_date']
    
    fieldsets = [
        ('User Info', {
            'fields': ['user']
        }),
        ('Job Info', {
            'fields': ['position', 'hire_date', 'salary']
        }),
        ('Personal Info', {
            'fields': [
                ('passport_series', 'passport_number'),
                'passport_issued_by', 'passport_issued_date',
                'address', 'birth_date'
            ]
        }),
        ('Emergency Contact', {
            'fields': [
                ('emergency_contact_name', 'emergency_contact_phone')
            ]
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'parent_name', 'parent_phone',
        'school_name', 'school_grade', 'age', 'is_active'
    ]
    list_filter = ['school_grade', 'is_active', 'birth_date']
    search_fields = [
        'user__first_name', 'user__last_name',
        'user__username', 'parent_name', 'school_name'
    ]
    ordering = ['-created_at']
    
    fieldsets = [
        ('User Info', {
            'fields': ['user', 'avatar']
        }),
        ('Parent Info', {
            'fields': [
                ('parent_name', 'parent_phone')
            ]
        }),
        ('Personal Info', {
            'fields': [
                'address', 'birth_date'
            ]
        }),
        ('School Info', {
            'fields': [
                ('school_name', 'school_grade')
            ]
        }),
        ('Additional Info', {
            'fields': ['medical_info', 'notes']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def age(self, obj):
        return obj.age
    age.short_description = 'Age'