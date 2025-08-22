from django.contrib import admin
from django.utils.html import format_html
from .models import Room, RoomBooking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'location', 'is_deleted', 'created_at']  # is_active -> is_deleted
    list_filter = ['is_deleted', 'capacity', 'created_at']
    search_fields = ['name', 'location']
    ordering = ['name']

    fieldsets = [
        ('Basic Info', {
            'fields': ['name', 'capacity', 'location']
        }),
        ('Details', {
            'fields': ['equipment', 'notes']
        }),
        ('Status', {
            'fields': ['is_deleted']
        })
    ]

@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ['room', 'date', 'time_slot', 'group', 'status', 'duration_hours', 'is_current', 'created_at']
    list_filter = ['status', 'date', 'room', 'created_at']
    search_fields = ['room__name', 'group__name', 'purpose']
    ordering = ['-date', '-start_time']

    fieldsets = [
        ('Booking Info', {
            'fields': ['room', 'date', ('start_time', 'end_time'), 'group']
        }),
        ('Details', {
            'fields': ['purpose', 'notes']
        }),
        ('Status', {
            'fields': ['status']
        })
    ]

    def time_slot(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    time_slot.short_description = 'Time Slot'

    def duration_hours(self, obj):
        return f"{obj.duration_hours:.1f}h"
    duration_hours.short_description = 'Duration'

    def is_current(self, obj):
        if obj.is_current:
            return format_html('<span style="color: green; font-weight: bold;">●</span>')
        return format_html('<span style="color: gray;">○</span>')
    is_current.short_description = 'Current'
