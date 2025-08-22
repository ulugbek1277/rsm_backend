from django.db import models
from django.utils import timezone
from core.models import BaseModel
from accounts.models import User


class SmsTemplate(BaseModel):
    """
    SMS template with placeholders
    """
    code = models.CharField(max_length=50, unique=True, help_text="Template kodi")
    name = models.CharField(max_length=100, help_text="Template nomi")
    text = models.TextField(help_text="SMS matni (placeholderlar bilan)")
    description = models.TextField(blank=True, help_text="Template tavsifi")
    
    class Meta:
        db_table = 'messaging_template'
        verbose_name = 'SMS Template'
        verbose_name_plural = 'SMS Templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def render(self, context):
        """
        Render template with context variables
        """
        text = self.text
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            text = text.replace(placeholder, str(value))
        return text
    
    @classmethod
    def get_default_templates(cls):
        defaults = [
            {
                'code': 'ABSENCE_NOTIFICATION',
                'name': 'Yo\'qlik haqida xabar',
                'text': 'Hurmatli {parent_name}, {student_name} bugun {date} sanasida {group_name} darsiga kelmadi. Ma\'lumot uchun: {center_phone}',
                'description': 'O\'quvchi darsga kelmagan holda ota-onaga yuboriladi'
            },
            {
                'code': 'SCHEDULE_CHANGE',
                'name': 'Jadval o\'zgarishi',
                'text': 'Hurmatli ota-onalar, {date} sanasida {group_name} guruhi darsi {status}. {note} Ma\'lumot: {center_phone}',
                'description': 'Dars jadvali o\'zgarganda yuboriladi'
            },
            {
                'code': 'PAYMENT_REMINDER',
                'name': 'To\'lov eslatmasi',
                'text': 'Hurmatli {parent_name}, {student_name} uchun {amount} so\'m to\'lov {due_date} sanasigacha amalga oshirilishi kerak. Ma\'lumot: {center_phone}',
                'description': 'To\'lov muddati yaqinlashganda yuboriladi'
            },
            {
                'code': 'DEBT_NOTIFICATION',
                'name': 'Qarz haqida xabar',
                'text': 'Hurmatli {parent_name}, {student_name} uchun {debt_amount} so\'m qarz mavjud. Iltimos, tezroq to\'lang. Ma\'lumot: {center_phone}',
                'description': 'Qarzdorlik haqida xabar'
            }
        ]
        return defaults


class SmsLog(BaseModel):
    """
    SMS sending log
    """
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('sent', 'Yuborildi'),
        ('delivered', 'Yetkazildi'),
        ('failed', 'Xatolik'),
        ('rejected', 'Rad etildi'),
    ]
    
    recipient_phone = models.CharField(max_length=13, help_text="Qabul qiluvchi telefon")
    message = models.TextField(help_text="SMS matni")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_id = models.CharField(max_length=100, blank=True, help_text="Provider ID")
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Xatolik matni")
    template = models.ForeignKey(
        SmsTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs'
    )
    
    class Meta:
        db_table = 'messaging_sms_log'
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.recipient_phone} - {self.get_status_display()}"
    
    def mark_as_sent(self, provider_id=None):
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_id:
            self.provider_id = provider_id
        self.save()
    
    def mark_as_delivered(self):
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save()


class Broadcast(BaseModel):
    """
    SMS broadcast to multiple recipients
    """
    AUDIENCE_CHOICES = [
        ('all_students', 'Barcha o\'quvchilar'),
        ('all_parents', 'Barcha ota-onalar'),
        ('group_students', 'Guruh o\'quvchilari'),
        ('group_parents', 'Guruh ota-onalari'),
        ('debtors', 'Qarzdorlar'),
        ('custom', 'Maxsus ro\'yxat'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('scheduled', 'Rejalashtirilgan'),
        ('sending', 'Yuborilmoqda'),
        ('completed', 'Yakunlangan'),
        ('failed', 'Xatolik'),
    ]
    
    title = models.CharField(max_length=200, help_text="Broadcast nomi")
    content = models.TextField(help_text="SMS matni")
    audience_type = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    target_group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Agar guruh tanlangan bo'lsa"
    )
    custom_phones = models.TextField(blank=True, help_text="Maxsus telefon raqamlar (har qatorga bittadan)")
    scheduled_for = models.DateTimeField(default=timezone.now, help_text="Yuborish vaqti")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'messaging_broadcast'
        verbose_name = 'Broadcast'
        verbose_name_plural = 'Broadcasts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def get_recipients(self):
        phones = []
        if self.audience_type == 'all_students':
            phones = list(User.objects.filter(role=User.STUDENT, is_active=True).values_list('phone', flat=True))
        elif self.audience_type == 'all_parents':
            phones = list(User.objects.filter(role=User.STUDENT, is_active=True, student_profile__isnull=False).values_list('student_profile__parent_phone', flat=True))
        elif self.audience_type == 'group_students' and self.target_group:
            phones = list(self.target_group.students.filter(is_active=True).values_list('student__phone', flat=True))
        elif self.audience_type == 'group_parents' and self.target_group:
            phones = list(self.target_group.students.filter(is_active=True, student__student_profile__isnull=False).values_list('student__student_profile__parent_phone', flat=True))
        elif self.audience_type == 'debtors':
            from payments.models import Invoice
            debtor_students = User.objects.filter(role=User.STUDENT, invoices__status__in=['pending','partial','overdue'], invoices__is_active=True, student_profile__isnull=False).distinct()
            phones = list(debtor_students.values_list('student_profile__parent_phone', flat=True))
        elif self.audience_type == 'custom':
            phones = [phone.strip() for phone in self.custom_phones.split('\n') if phone.strip()]
        return list(set([phone for phone in phones if phone]))
    
    def start_sending(self):
        recipients = self.get_recipients()
        self.total_recipients = len(recipients)
        self.status = 'sending'
        self.started_at = timezone.now()
        self.save()
        from .tasks import send_broadcast_sms
        send_broadcast_sms.delay(self.id)
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def success_rate(self):
        if self.total_recipients == 0:
            return 0
        return round((self.sent_count / self.total_recipients) * 100, 1)