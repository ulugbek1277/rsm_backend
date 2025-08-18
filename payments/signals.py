from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Payment, Invoice


@receiver(post_save, sender=Payment)
def update_invoice_status_on_payment_save(sender, instance, **kwargs):
    """
    Update invoice status when payment is saved
    """
    instance.invoice.update_status()


@receiver(post_delete, sender=Payment)
def update_invoice_status_on_payment_delete(sender, instance, **kwargs):
    """
    Update invoice status when payment is deleted
    """
    instance.invoice.update_status()
