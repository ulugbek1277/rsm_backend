from django.db import models
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Abstract base class with created_at and updated_at fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class AuditableModel(TimeStampedModel):
    """
    Abstract base class with audit trail functionality
    """
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_updated'
    )
    history = HistoricalRecords(inherit=True)
    
    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    """Manager that returns only active objects"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteModel(models.Model):
    """
    Abstract base class with soft delete functionality
    """
    is_active = models.BooleanField(default=True)
    
    objects = models.Manager()  # Default manager
    active = ActiveManager()    # Active objects only
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete - mark as inactive instead of deleting"""
        self.is_active = False
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the object"""
        super().delete(using=using, keep_parents=keep_parents)