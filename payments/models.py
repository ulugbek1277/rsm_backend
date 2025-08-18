from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.core.models import AuditableModel, SoftDeleteModel
from apps.accounts.models import User


class Invoice(AuditableModel, SoftDeleteModel):
    """
    Invoice model for student payments
    """
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
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="To'lov miqdori (so'm)"
    )
    due_date = models.DateField(help_text="To'lov muddati")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, help_text="To'lov tavsifi")
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Chegirma miqdori"
    )
    
    class Meta:
        db_table = 'payments_invoice'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.student.get_full_name()} - {self.amount} so'm"
    
    def clean(self):
        """
        Validate invoice constraints
        """
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
        """Calculate final amount after discount"""
        return self.amount - self.discount_amount
    
    @property
    def paid_amount(self):
        """Calculate total paid amount"""
        return self.payments.aggregate(
            total=models.Sum('paid_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to pay"""
        return self.final_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    def update_status(self):
        """Update invoice status based on payments"""
        paid = self.paid_amount
        final = self.final_amount
        
        if paid >= final:
            self.status = 'paid'
        elif paid > 0:
            self.status = 'partial'
        elif self.is_overdue:
            self.status = 'overdue'
        else:
            self.status = 'pending'
        
        # Save without triggering signals to avoid recursion
        Invoice.objects.filter(id=self.id).update(status=self.status)


class Payment(AuditableModel, SoftDeleteModel):
    """
    Payment model for tracking payments
    """
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
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="To'langan miqdor (so'm)"
    )
    paid_at = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    note = models.TextField(blank=True, help_text="To'lov haqida eslatma")
    receipt_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-paid_at']
    
    def __str__(self):
        return f"Payment #{self.id} - {self.paid_amount} so'm - {self.invoice.student.get_full_name()}"
    
    def clean(self):
        """
        Validate payment constraints
        """
        if self.paid_amount <= 0:
            raise ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak")
        
        # Check if payment doesn't exceed remaining amount
        remaining = self.invoice.remaining_amount
        if self.paid_amount > remaining:
            raise ValidationError(
                f"To'lov miqdori qolgan miqdordan ({remaining} so'm) oshmasligi kerak"
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Update invoice status
        self.invoice.update_status()


class DebtSnapshot(AuditableModel):
    """
    Periodic snapshot of student debts for reporting
    """
    snapshot_date = models.DateField(default=timezone.now)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='debt_snapshots',
        limit_choices_to={'role': User.STUDENT}
    )
    total_debt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Umumiy qarz miqdori (so'm)"
    )
    overdue_debt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Muddati o'tgan qarz miqdori"
    )
    overdue_days = models.PositiveIntegerField(
        default=0,
        help_text="Eng eski qarzning muddati o'tgan kunlari"
    )
    
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
        """
        Create debt snapshot for a student
        """
        if date is None:
            date = timezone.now().date()
        
        # Calculate total debt
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
        
        # Create or update snapshot
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
        """
        Create debt snapshots for all students with debt
        """
        if date is None:
            date = timezone.now().date()
        
        # Get all students with unpaid invoices
        students_with_debt = User.objects.filter(
            role=User.STUDENT,
            invoices__status__in=['pending', 'partial', 'overdue'],
            invoices__is_active=True
        ).distinct()
        
        snapshots = []
        for student in students_with_debt:
            snapshot = cls.create_snapshot(student, date)
            snapshots.append(snapshot)
        
        return snapshots
