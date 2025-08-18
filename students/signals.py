from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Student, StudentEnrollment


@receiver(post_save, sender=StudentEnrollment)
def update_student_enrollment_status(sender, instance, created, **kwargs):
    """Update student status when enrollment changes"""
    if created and instance.status == 'active':
        # Set student as active when enrolled in a course
        if instance.student.status == 'inactive':
            instance.student.status = 'active'
            instance.student.save(update_fields=['status'])


@receiver(post_delete, sender=StudentEnrollment)
def check_student_status_on_enrollment_delete(sender, instance, **kwargs):
    """Check if student should be inactive when enrollment is deleted"""
    student = instance.student
    active_enrollments = student.enrollments.filter(status='active').count()
    
    if active_enrollments == 0 and student.status == 'active':
        student.status = 'inactive'
        student.save(update_fields=['status'])
