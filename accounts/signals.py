from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmployeeProfile, StudentProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create profile based on user role
    """
    if created:
        if instance.is_staff_member:
            EmployeeProfile.objects.get_or_create(user=instance)
        elif instance.is_student:
            StudentProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'parent_name': '',
                    'parent_phone': '',
                    'address': '',
                    'birth_date': '2000-01-01'
                }
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save profile when user is saved
    """
    if instance.is_staff_member and hasattr(instance, 'employee_profile'):
        instance.employee_profile.save()
    elif instance.is_student and hasattr(instance, 'student_profile'):
        instance.student_profile.save()