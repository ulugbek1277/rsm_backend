from rest_framework import serializers
from .models import GlobalSettings, UserSettings, SettingsCategory, SettingsBackup


class GlobalSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = GlobalSettings
        fields = [
            'id', 'key', 'value', 'typed_value', 'setting_type', 
            'description', 'category', 'is_active', 'is_public',
            'created_at', 'updated_at'
        ]

    def get_typed_value(self, obj):
        return obj.get_value()

    def validate_value(self, value):
        """Validate value based on setting type"""
        setting_type = self.initial_data.get('setting_type', 'string')
        
        if setting_type == 'integer':
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("Butun son bo'lishi kerak")
        elif setting_type == 'float':
            try:
                float(value)
            except ValueError:
                raise serializers.ValidationError("O'nlik son bo'lishi kerak")
        elif setting_type == 'json':
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Yaroqli JSON bo'lishi kerak")
        
        return value


class UserSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = UserSettings
        fields = [
            'id', 'user', 'user_name', 'key', 'value', 'typed_value', 
            'setting_type', 'created_at', 'updated_at'
        ]

    def get_typed_value(self, obj):
        return obj.get_value()


class SettingsCategorySerializer(serializers.ModelSerializer):
    settings_count = serializers.SerializerMethodField()

    class Meta:
        model = SettingsCategory
        fields = [
            'id', 'name', 'display_name', 'description', 'icon', 
            'order', 'is_active', 'settings_count'
        ]

    def get_settings_count(self, obj):
        return obj.get_settings().count()


class SettingsBackupSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    settings_count = serializers.SerializerMethodField()

    class Meta:
        model = SettingsBackup
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_name',
            'settings_count', 'created_at'
        ]
        read_only_fields = ['created_by', 'settings_data']

    def get_settings_count(self, obj):
        return len(obj.settings_data)


class SettingsExportSerializer(serializers.Serializer):
    """Serializer for settings export"""
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Eksport qilinadigan kategoriyalar ro'yxati"
    )
    include_inactive = serializers.BooleanField(
        default=False,
        help_text="Nofaol sozlamalarni ham qo'shish"
    )


class SettingsImportSerializer(serializers.Serializer):
    """Serializer for settings import"""
    settings_data = serializers.JSONField(
        help_text="Import qilinadigan sozlamalar ma'lumotlari"
    )
    overwrite_existing = serializers.BooleanField(
        default=False,
        help_text="Mavjud sozlamalarni qayta yozish"
    )
