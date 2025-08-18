from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import AuditableModel, SoftDeleteModel
from apps.accounts.models import User


class Group(AuditableModel, SoftDeleteModel):
    """
    Group model for student groups
    """
    STATUS_CHOICES = [
        ('planning', 'Rejalashtirilmoqda'),
        ('active', 'Faol'),
        ('completed', 'Yakunlangan'),
        ('archived', 'Arxivlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='groups'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_groups',
        limit_choices_to={'role': User.TEACHER}
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )
    planned_start = models.DateField(help_text="Rejalashtirilgan boshlanish sanasi")
    planned_end = models.DateField(help_text="Rejalashtirilgan tugash sanasi")
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups'
    )
    max_students = models.PositiveIntegerField(
        help_text="Maksimal o'quvchilar soni"
    )
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'groups_group'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.title}"
    
    def clean(self):
        """
        Validate group constraints
        """
        if self.planned_start >= self.planned_end:
            raise ValidationError("Boshlanish sanasi tugash sanasidan oldin bo'lishi kerak")
        
        if self.actual_start and self.actual_end:
            if self.actual_start >= self.actual_end:
                raise ValidationError("Haqiqiy boshlanish sanasi tugash sanasidan oldin bo'lishi kerak")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def current_students_count(self):
        """Count of currently active students"""
        return self.students.filter(is_active=True).count()
    
    @property
    def available_spots(self):
        """Available spots for new students"""
        return self.max_students - self.current_students_count
    
    @property
    def is_full(self):
        """Check if group is full"""
        return self.current_students_count >= self.max_students
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage based on dates"""
        if not self.actual_start:
            return 0
        
        if self.actual_end:
            return 100
        
        today = timezone.now().date()
        if today < self.actual_start:
            return 0
        
        total_days = (self.planned_end - self.actual_start).days
        elapsed_days = (today - self.actual_start).days
        
        if total_days <= 0:
            return 100
        
        percentage = min(100, max(0, (elapsed_days / total_days) * 100))
        return round(percentage, 1)


class GroupStudent(AuditableModel, SoftDeleteModel):
    """
    Many-to-many relationship between Group and Student with additional fields
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='students'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='groups',
        limit_choices_to={'role': User.STUDENT}
    )
    joined_at = models.DateField(default=timezone.now)
    left_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Qo'shimcha eslatmalar")
    
    class Meta:
        db_table = 'groups_student'
        verbose_name = 'Group Student'
        verbose_name_plural = 'Group Students'
        unique_together = ['group', 'student']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.name}"
    
    def clean(self):
        """
        Validate group student constraints
        """
        if self.left_at and self.joined_at >= self.left_at:
            raise ValidationError("Qo'shilish sanasi chiqish sanasidan oldin bo'lishi kerak")
        
        # Check if group is full (excluding current student if updating)
        if self.group.is_full and not self.pk:
            raise ValidationError(f"{self.group.name} guruhi to'liq")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_currently_active(self):
        """Check if student is currently active in group"""
        return self.is_active and not self.left_at
    
    @property
    def duration_days(self):
        """Calculate duration in group"""
        end_date = self.left_at or timezone.now().date()
        return (end_date - self.joined_at).days
