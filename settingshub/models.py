from django.db import models
from django.core.cache import cache
from core.models import BaseModel


class GlobalSettings(BaseModel):
    """Global system settings"""
    
    SETTING_TYPES = [
        ('string', 'Matn'),
        ('integer', 'Butun son'),
        ('float', 'O\'nlik son'),
        ('boolean', 'Ha/Yo\'q'),
        ('json', 'JSON'),
        ('text', 'Uzun matn'),
    ]

    key = models.CharField(max_length=100, unique=True, verbose_name="Kalit")
    value = models.TextField(verbose_name="Qiymat")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string', verbose_name="Tur")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    category = models.CharField(max_length=50, default='general', verbose_name="Kategoriya")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_public = models.BooleanField(default=False, verbose_name="Ommaviy")

    class Meta:
        verbose_name = "Global sozlama"
        verbose_name_plural = "Global sozlamalar"
        ordering = ['category', 'key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    def get_value(self):
        """Get typed value"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'json':
            import json
            return json.loads(self.value)
        return self.value

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache when setting is updated
        cache.delete(f'setting_{self.key}')
        cache.delete('all_settings')

    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value with caching"""
        cache_key = f'setting_{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(key=key, is_active=True)
                value = setting.get_value()
                cache.set(cache_key, value, 3600)  # Cache for 1 hour
            except cls.DoesNotExist:
                value = default
                
        return value

    @classmethod
    def get_all_settings(cls, category=None, public_only=False):
        """Get all settings as dictionary"""
        cache_key = f'all_settings_{category}_{public_only}'
        settings_dict = cache.get(cache_key)
        
        if settings_dict is None:
            queryset = cls.objects.filter(is_active=True)
            
            if category:
                queryset = queryset.filter(category=category)
            if public_only:
                queryset = queryset.filter(is_public=True)
                
            settings_dict = {
                setting.key: setting.get_value() 
                for setting in queryset
            }
            cache.set(cache_key, settings_dict, 3600)
            
        return settings_dict


class UserSettings(BaseModel):
    """User-specific settings"""
    
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE, 
        related_name='custom_settings',
        verbose_name="Foydalanuvchi"
    )
    key = models.CharField(max_length=100, verbose_name="Kalit")
    value = models.TextField(verbose_name="Qiymat")
    setting_type = models.CharField(
        max_length=20, 
        choices=GlobalSettings.SETTING_TYPES, 
        default='string',
        verbose_name="Tur"
    )

    class Meta:
        verbose_name = "Foydalanuvchi sozlamasi"
        verbose_name_plural = "Foydalanuvchi sozlamalari"
        unique_together = ['user', 'key']
        ordering = ['user', 'key']

    def __str__(self):
        return f"{self.user.username} - {self.key}: {self.value}"

    def get_value(self):
        """Get typed value"""
        if self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes', 'on']
        elif self.setting_type == 'json':
            import json
            return json.loads(self.value)
        return self.value

    @classmethod
    def get_user_setting(cls, user, key, default=None):
        """Get user setting value"""
        try:
            setting = cls.objects.get(user=user, key=key)
            return setting.get_value()
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_user_setting(cls, user, key, value, setting_type='string'):
        """Set user setting value"""
        setting, created = cls.objects.get_or_create(
            user=user, 
            key=key,
            defaults={'value': str(value), 'setting_type': setting_type}
        )
        if not created:
            setting.value = str(value)
            setting.setting_type = setting_type
            setting.save()
        return setting


class SettingsCategory(BaseModel):
    """Settings categories for organization"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    display_name = models.CharField(max_length=100, verbose_name="Ko'rsatiladigan nom")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Ikonka")
    order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Sozlamalar kategoriyasi"
        verbose_name_plural = "Sozlamalar kategoriyalari"
        ordering = ['order', 'name']

    def __str__(self):
        return self.display_name

    def get_settings(self):
        """Get all settings in this category"""
        return GlobalSettings.objects.filter(category=self.name, is_active=True)


class SettingsBackup(BaseModel):
    """Settings backup for restore functionality"""
    
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    settings_data = models.JSONField(verbose_name="Sozlamalar ma'lumotlari")
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE,
        verbose_name="Yaratuvchi"
    )

    class Meta:
        verbose_name = "Sozlamalar zaxirasi"
        verbose_name_plural = "Sozlamalar zaxiralari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def restore_settings(self):
        """Restore settings from backup"""
        for key, data in self.settings_data.items():
            GlobalSettings.objects.update_or_create(
                key=key,
                defaults={
                    'value': data['value'],
                    'setting_type': data['setting_type'],
                    'description': data.get('description', ''),
                    'category': data.get('category', 'general'),
                    'is_active': data.get('is_active', True),
                    'is_public': data.get('is_public', False),
                }
            )
        
        # Clear cache
        cache.clear()

    @classmethod
    def create_backup(cls, name, description, user):
        """Create settings backup"""
        settings_data = {}
        for setting in GlobalSettings.objects.all():
            settings_data[setting.key] = {
                'value': setting.value,
                'setting_type': setting.setting_type,
                'description': setting.description,
                'category': setting.category,
                'is_active': setting.is_active,
                'is_public': setting.is_public,
            }
        
        return cls.objects.create(
            name=name,
            description=description,
            settings_data=settings_data,
            created_by=user
        )
