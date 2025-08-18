from django.db import models
from django.utils.text import slugify
from apps.core.models import AuditableModel, SoftDeleteModel
from apps.core.utils import generate_slug


class Course(AuditableModel, SoftDeleteModel):
    """
    Course model for educational programs
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Oylik to'lov miqdori (so'm)"
    )
    duration_months = models.PositiveIntegerField(
        help_text="Kurs davomiyligi (oy)"
    )
    max_students = models.PositiveIntegerField(
        default=15,
        help_text="Maksimal o'quvchilar soni"
    )
    prerequisites = models.TextField(
        blank=True,
        help_text="Kursga kirish uchun talablar"
    )
    objectives = models.TextField(
        blank=True,
        help_text="Kurs maqsadlari"
    )
    syllabus = models.TextField(
        blank=True,
        help_text="O'quv dasturi"
    )
    certificate_template = models.FileField(
        upload_to='courses/certificates/',
        null=True,
        blank=True,
        help_text="Sertifikat shabloni"
    )
    
    class Meta:
        db_table = 'courses_course'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.title)
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total course price"""
        return self.price_monthly * self.duration_months
    
    @property
    def active_groups_count(self):
        """Count of active groups for this course"""
        return self.groups.filter(status='active').count()
