from django.db import models
from django.conf import settings

class AbsenceReason(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class AttendanceSession(models.Model):
    date = models.DateField()
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.group} - {self.date}"


class AttendanceRecord(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    status_choices = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='present')
    reason = models.ForeignKey(AbsenceReason, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"