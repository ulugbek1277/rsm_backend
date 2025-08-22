from django.contrib import admin
from .models import AbsenceReason, AttendanceSession, AttendanceRecord

@admin.register(AbsenceReason)
class AbsenceReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')  # name o‘rniga title qo‘ydik
    search_fields = ('title',)

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'date')
    search_fields = ('group__name',)
    list_filter = ('date', 'group')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'session', 'status')
    search_fields = ('student__full_name', 'session__group__name')
    list_filter = ('status',)