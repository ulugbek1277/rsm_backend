from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel


class Lesson(BaseModel):
    """
    Regular weekly lesson schedule
    """
    WEEKDAY_CHOICES = [
        (0, 'Dushanba'),
        (1, 'Seshanba'),
        (2, 'Chorshanba'),
        (3, 'Payshanba'),
        (4, 'Juma'),
        (5, 'Shanba'),
        (6, 'Yakshanba'),
    ]
    
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        db_table = 'schedules_lesson'
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        unique_together = ['group', 'weekday', 'start_time']
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.group.name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """
        Validate lesson constraints
        """
        if self.start_time >= self.end_time:
            raise ValidationError("Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak")
        
        # Check room availability for this time slot
        conflicting_lessons = Lesson.objects.filter(
            room=self.room,
            weekday=self.weekday,
            is_active=True
        ).exclude(pk=self.pk)
        
        for lesson in conflicting_lessons:
            if (self.start_time < lesson.end_time and self.end_time > lesson.start_time):
                raise ValidationError(
                    f"{self.room.name} xonasi {self.get_weekday_display()} kuni "
                    f"{lesson.start_time}-{lesson.end_time} vaqtida band"
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_hours(self):
        """Calculate lesson duration in hours"""
        from datetime import datetime
        start = datetime.combine(timezone.now().date(), self.start_time)
        end = datetime.combine(timezone.now().date(), self.end_time)
        return (end - start).total_seconds() / 3600
    
    def get_next_occurrence(self):
        """Get next occurrence date for this lesson"""
        today = timezone.now().date()
        days_ahead = self.weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timezone.timedelta(days=days_ahead)


class CalendarOverride(BaseModel):
    """
    Calendar overrides for holidays, cancellations, or special events
    """
    date = models.DateField()
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='calendar_overrides',
        null=True,
        blank=True,
        help_text="Bo'sh qoldirsa barcha guruhlarga tegishli"
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='calendar_overrides',
        null=True,
        blank=True
    )
    is_canceled = models.BooleanField(
        default=True,
        help_text="Dars bekor qilinganmi yoki o'zgartirilganmi"
    )
    alternative_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Agar vaqt o'zgartirilgan bo'lsa"
    )
    alternative_room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='alternative_overrides',
        null=True,
        blank=True,
        help_text="Agar xona o'zgartirilgan bo'lsa"
    )
    note = models.TextField(blank=True, help_text="Sabab yoki qo'shimcha ma'lumot")
    notify_students = models.BooleanField(
        default=True,
        help_text="O'quvchilarga SMS yuborilsinmi"
    )
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'schedules_override'
        verbose_name = 'Calendar Override'
        verbose_name_plural = 'Calendar Overrides'
        ordering = ['-date']
    
    def __str__(self):
        group_name = self.group.name if self.group else "Barcha guruhlar"
        status = "Bekor qilingan" if self.is_canceled else "O'zgartirilgan"
        return f"{group_name} - {self.date} ({status})"
    
    def clean(self):
        """
        Validate calendar override
        """
        if self.date < timezone.now().date():
            raise ValidationError("O'tgan sanaga override qo'yib bo'lmaydi")
        
        if not self.is_canceled and not self.alternative_time and not self.alternative_room:
            raise ValidationError(
                "Agar dars bekor qilinmagan bo'lsa, alternativ vaqt yoki xona ko'rsatilishi kerak"
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Send notification if needed
        if self.notify_students and not self.notification_sent:
            self.send_notification()
    
    def send_notification(self):
        """
        Send SMS notification about schedule change
        """
        from messaging.tasks import send_schedule_change_notification
        
        # Queue SMS notification task
        send_schedule_change_notification.delay(self.id)
        
        self.notification_sent = True
        super().save(update_fields=['notification_sent'])
