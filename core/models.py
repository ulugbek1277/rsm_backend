from django.db import models
from django.conf import settings
from django.utils import timezone

# =======================
# Mixins
# =======================

class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditableMixin(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False, user=None):
        """
        Soft delete: marks the record as inactive instead of removing it from the DB.
        If user is provided, set updated_by.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        if hasattr(self, 'updated_by') and user:
            self.updated_by = user
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanently deletes the record from the DB.
        """
        models.Model.delete(self, using=using, keep_parents=keep_parents)

    class Meta:
        abstract = True


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def deleted(self):
        return super().get_queryset().filter(is_active=False)


class BaseModel(TimeStampedMixin, AuditableMixin, SoftDeleteMixin):
    """
    Common base model combining timestamp, audit, and soft delete features.
    """
    objects = models.Manager()  # Default manager
    active = ActiveManager()    # Only active records

    class Meta:
        abstract = True
        ordering = ['-created_at']  # Latest first
