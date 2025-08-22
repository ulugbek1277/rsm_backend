from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel

User = get_user_model()


class Task(BaseModel):
    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', 'O\'rta'),
        ('high', 'Yuqori'),
        ('urgent', 'Shoshilinch'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    title = models.CharField('Sarlavha', max_length=200)
    description = models.TextField('Tavsif', blank=True)
    priority = models.CharField('Muhimlik', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('Holat', max_length=15, choices=STATUS_CHOICES, default='pending')
    
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_tasks',
        verbose_name='Tayinlangan'
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        verbose_name='Tayinlovchi'
    )
    
    due_date = models.DateTimeField('Muddat', null=True, blank=True)
    completed_at = models.DateTimeField('Bajarilgan vaqt', null=True, blank=True)
    
    # File attachment
    attachment = models.FileField('Fayl', upload_to='tasks/attachments/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Vazifa'
        verbose_name_plural = 'Vazifalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False


class TaskComment(BaseModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField('Izoh')
    
    class Meta:
        verbose_name = 'Vazifa izohi'
        verbose_name_plural = 'Vazifa izohlari'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.task.title} - {self.author.get_full_name()}"
