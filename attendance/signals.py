from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AttendanceRecord


@receiver(post_save, sender=AttendanceRecord)
def handle_attendance_record_save(sender, instance, created, **kwargs):
    """
    Handle attendance record save - send notifications if needed
    """
    if created and instance.status == 'absent_unexcused':
        # Notification will be sent via the model's save method
        pass
