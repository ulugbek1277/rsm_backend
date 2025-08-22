from django.contrib import admin
from .models import Student, StudentEnrollment, StudentDocument, StudentNote


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'phone', 'status', 'enrollment_date', 
        'total_debt', 'education_level'
    ]
    list_filter = ['status', 'gender', 'education_level', 'region', 'enrollment_date']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['enrollment_date', 'total_debt', 'last_payment_date']
    
    fieldsets = (
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('user', 'first_name', 'last_name', 'middle_name', 
                       'birth_date', 'gender', 'photo')
        }),
        ('Aloqa ma\'lumotlari', {
            'fields': ('phone', 'email', 'region', 'district', 'address')
        }),
        ('Ta\'lim ma\'lumotlari', {
            'fields': ('education_level', 'school_name')
        }),
        ('Ota-ona ma\'lumotlari', {
            'fields': ('parent_name', 'parent_phone')
        }),
        ('Holat va kuzatuv', {
            'fields': ('status', 'enrollment_date', 'total_debt', 'last_payment_date', 'notes')
        }),
    )

    # Admin list_display ichida property ishlashini ta'minlash
    def full_name(self, obj):
        return obj.full_name
    full_name.admin_order_field = 'first_name'
    full_name.short_description = 'To\'liq ism'


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrollment_date', 'progress_percentage']
    list_filter = ['status', 'course', 'enrollment_date']
    search_fields = ['student__first_name', 'student__last_name', 'course__title']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'title', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'title']


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ['student', 'note_type', 'title', 'author', 'is_important', 'created_at']
    list_filter = ['note_type', 'is_important', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'title', 'content']