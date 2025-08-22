from django.db import models
from django.core.cache import cache
from core.models import BaseModel


class SystemSettings(BaseModel):
    SETTING_TYPES = [
        ('text', 'Matn'),
        ('number', 'Raqam'),
        ('boolean', 'Ha/Yo\'q'),
        ('json', 'JSON'),
    ]

    key = models.CharField('Kalit', max_length=100, unique=True)
    value = models.TextField('Qiymat')
    setting_type = models.CharField('Tur', max_length=10, choices=SETTING_TYPES, default='text')
    description = models.TextField('Tavsif', blank=True)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Tizim sozlamasi'
        verbose_name_plural = 'Tizim sozlamalari'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Cache ni tozalash
        cache.delete(f'setting_{self.key}')

    @classmethod
    def get_setting(cls, key, default=None):
        """Sozlamani olish (cache bilan)"""
        cache_key = f'setting_{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(key=key, is_active=True)
                value = setting.get_typed_value()
                cache.set(cache_key, value, 3600)  # 1 soat cache
            except cls.DoesNotExist:
                value = default
                
        return value

    def get_typed_value(self):
        """Qiymatni to'g'ri turga o'tkazish"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'number':
            try:
                return float(self.value) if '.' in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.setting_type == 'json':
            import json
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value


class NotificationSettings(BaseModel):
    """Xabarnoma sozlamalari"""
    sms_enabled = models.BooleanField('SMS yoqilgan', default=True)
    sms_absence_enabled = models.BooleanField('Darsga kelmagan uchun SMS', default=True)
    sms_payment_reminder = models.BooleanField('To\'lov eslatmasi SMS', default=True)
    sms_debt_warning = models.BooleanField('Qarz ogohlantirish SMS', default=True)
    
    # SMS shablon sozlamalari
    absence_sms_template = models.TextField(
        'Darsga kelmagan SMS shabloni',
        default='Hurmatli {parent_name}, {student_name} bugun {date} kuni darsga kelmadi.'
    )
    payment_reminder_template = models.TextField(
        'To\'lov eslatmasi shabloni',
        default='Hurmatli {parent_name}, {student_name} uchun {amount} so\'m to\'lov muddati yetdi.'
    )
    debt_warning_template = models.TextField(
        'Qarz ogohlantirish shabloni',
        default='Hurmatli {parent_name}, {student_name} uchun {debt_amount} so\'m qarz mavjud.'
    )

    class Meta:
        verbose_name = 'Xabarnoma sozlamasi'
        verbose_name_plural = 'Xabarnoma sozlamalari'

    def __str__(self):
        return f"Xabarnoma sozlamalari - {self.created_at.date()}"


class PaymentSettings(BaseModel):
    """To'lov sozlamalari"""
    default_currency = models.CharField('Asosiy valyuta', max_length=3, default='UZS')
    late_payment_fee = models.DecimalField('Kechikish jarimi (%)', max_digits=5, decimal_places=2, default=0)
    payment_due_days = models.IntegerField('To\'lov muddati (kun)', default=30)
    debt_warning_days = models.IntegerField('Qarz ogohlantirish (kun)', default=7)
    
    # Chegirma sozlamalari
    sibling_discount = models.DecimalField('Aka-uka chegirma (%)', max_digits=5, decimal_places=2, default=10)
    early_payment_discount = models.DecimalField('Erta to\'lov chegirma (%)', max_digits=5, decimal_places=2, default=5)

    class Meta:
        verbose_name = 'To\'lov sozlamasi'
        verbose_name_plural = 'To\'lov sozlamalari'

    def __str__(self):
        return f"To'lov sozlamalari - {self.default_currency}"
