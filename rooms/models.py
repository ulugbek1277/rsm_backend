from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import AuditableModel, SoftDeleteModel


class Room(AuditableModel, SoftDeleteModel):
    """
    Room model for classrooms
    """
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField(help_text="Maksimal o'quvchilar soni")
    location = models.CharField(max_length=200, blank=True, help_text="Xona joylashuvi")
    equipment = models.TextField(blank=True, help_text="Xona jihozlari")
    notes = models.TextField(blank=True, help_text="Qo'shimcha eslatmalar")
    
    class Meta:
        db_table = 'rooms_room'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (sig'imi: {self.capacity})"
    
    def is_available(self, date, start_time, end_time, exclude_booking=None):
        """
        Check if room is available for given time slot
        """
        bookings = self.bookings.filter(
            date=date,
            status__in=['confirmed', 'in_progress']
        )
        
        if exclude_booking:
            bookings = bookings.exclude(id=exclude_booking.id)
        
        for booking in bookings:
            if (start_time < booking.end_time and end_time > booking.start_time):
                return False
        return True


class RoomBooking(AuditableModel, SoftDeleteModel):
    """
    Room booking model for scheduling
    """
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='room_bookings'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    purpose = models.CharField(
        max_length=200,
        blank=True,
        help_text="Booking maqsadi"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'rooms_booking'
        verbose_name = 'Room Booking'
        verbose_name_plural = 'Room Bookings'
        ordering = ['date', 'start_time']
        unique_together = ['room', 'date', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.room.name} - {self.date} ({self.start_time}-{self.end_time})"
    
    def clean(self):
        """
        Validate booking constraints
        """
        if self.start_time >= self.end_time:
            raise ValidationError("Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak")
        
        if self.date < timezone.now().date():
            raise ValidationError("O'tgan sanaga booking qilib bo'lmaydi")
        
        # Check room availability
        if not self.room.is_available(
            self.date, self.start_time, self.end_time, exclude_booking=self
        ):
            raise ValidationError(
                f"{self.room.name} xonasi {self.date} sanasida "
                f"{self.start_time}-{self.end_time} vaqtida band"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_hours(self):
        """Calculate booking duration in hours"""
        from datetime import datetime, timedelta
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        duration = end - start
        return duration.total_seconds() / 3600
    
    @property
    def is_current(self):
        """Check if booking is currently active"""
        now = timezone.now()
        booking_start = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        booking_end = timezone.make_aware(
            timezone.datetime.combine(self.date, self.end_time)
        )
        return booking_start <= now <= booking_end
