from django.contrib import admin
from .models import Task, TaskComment


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'assigned_by', 'priority', 'status', 'due_date', 'is_overdue']
    list_filter = ['status', 'priority', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'assigned_to__first_name', 'assigned_to__last_name']
    readonly_fields = ['completed_at', 'created_at', 'updated_at']
    inlines = [TaskCommentInline]
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('title', 'description', 'priority', 'status')
        }),
        ('Tayinlash', {
            'fields': ('assigned_to', 'assigned_by', 'due_date')
        }),
        ('Fayl', {
            'fields': ('attachment',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi vazifa yaratilayotganda
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['task__title', 'author__first_name', 'author__last_name', 'comment']
    readonly_fields = ['created_at']
