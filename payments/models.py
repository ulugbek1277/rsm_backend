from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from core.models import BaseModel
from accounts.models import User


class Invoice(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('paid', 'To\'langan'),
        ('partial', 'Qisman to\'langan'),
        ('overdue', 'Muddati o\'tgan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        limit_choices_to={'role': User.STUDENT}
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'payments_invoice'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.student.get_full_name()} - {self.amount} so'm"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak")
        if self.discount_amount < 0:
            raise ValidationError("Chegirma miqdori manfiy bo'lishi mumkin emas")
        if self.discount_amount >= self.amount:
            raise ValidationError("Chegirma miqdori to'lov miqdoridan kam bo'lishi kerak")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        self.update_status()
    
    @property
    def final_amount(self):
        return self.amount - self.discount_amount
    
    @property
    def paid_amount(self):
        return self.payments.aggregate(total=models.Sum('paid_amount'))['total'] or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        return self.final_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    @property
    def days_overdue(self):
        return (timezone.now().date() - self.due_date).days if self.is_overdue else 0
    
    def update_status(self):
        paid = self.paid_amount
        final = self.final_amount
        if paid >= final:
            status = 'paid'
        elif paid > 0:
            status = 'partial'
        elif self.is_overdue:
            status = 'overdue'
        else:
            status = 'pending'
        if self.status != status:
            Invoice.objects.filter(id=self.id).update(status=status)
            self.status = status


class Payment(BaseModel):
    METHOD_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('transfer', 'O\'tkazma'),
        ('online', 'Onlayn'),
    ]
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    note = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-paid_at']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.paid_amount} so'm - {self.invoice.student.get_full_name()}"
    
    def clean(self):
        if self.paid_amount <= 0:
            raise ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak")
        if self.paid_amount > self.invoice.remaining_amount:
            raise ValidationError(f"To'lov miqdori qolgan miqdordan oshmasligi kerak")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        self.invoice.update_status()


class DebtSnapshot(BaseModel):
    snapshot_date = models.DateField(default=timezone.now)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='debt_snapshots',
        limit_choices_to={'role': User.STUDENT}
    )
    total_debt = models.DecimalField(max_digits=10, decimal_places=2)
    overdue_debt = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    overdue_days = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'payments_debt_snapshot'
        verbose_name = 'Debt Snapshot'
        verbose_name_plural = 'Debt Snapshots'
        unique_together = ['snapshot_date', 'student']
        ordering = ['-snapshot_date', 'student']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.snapshot_date} - {self.total_debt} so'm"
    
    @classmethod
    def create_snapshot(cls, student, date=None):
        if date is None:
            date = timezone.now().date()
        unpaid_invoices = Invoice.objects.filter(
            student=student,
            status__in=['pending', 'partial', 'overdue'],
            is_active=True
        )
        total_debt = Decimal('0.00')
        overdue_debt = Decimal('0.00')
        max_overdue_days = 0
        for invoice in unpaid_invoices:
            remaining = invoice.remaining_amount
            total_debt += remaining
            if invoice.is_overdue:
                overdue_debt += remaining
                max_overdue_days = max(max_overdue_days, invoice.days_overdue)
        snapshot, created = cls.objects.update_or_create(
            snapshot_date=date,
            student=student,
            defaults={
                'total_debt': total_debt,
                'overdue_debt': overdue_debt,
                'overdue_days': max_overdue_days
            }
        )
        return snapshot
    
    @classmethod
    def create_daily_snapshots(cls, date=None):
        if date is None:
            date = timezone.now().date()
        students_with_debt = User.objects.filter(
            role=User.STUDENT,
            invoices__status__in=['pending', 'partial', 'overdue'],
            invoices__is_active=True
        ).distinct()
        return [cls.create_snapshot(student, date) for student in students_with_debt]