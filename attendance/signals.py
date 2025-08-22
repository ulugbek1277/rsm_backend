from django.db.models.signals import post_save
from django.dispatch import receiver

# AttendanceRecord modelini string orqali chaqiramiz, shunda importdan circular error bo'lmaydi
@receiver(post_save, sender='attendance.AttendanceRecord')
def attendance_record_saved(sender, instance, created, **kwargs):
    if created:
        # Masalan, yangi AttendanceRecord qo'shilganda xabar yuborish logikasi
        print(f"New attendance record for {instance.student} on {instance.session.date}")