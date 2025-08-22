from rest_framework import serializers
from .models import Lesson, CalendarOverride
from core.serializers import BaseModelSerializer


class LessonSerializer(BaseModelSerializer):
    """
    Lesson serializer
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    next_occurrence = serializers.ReadOnlyField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'group', 'group_name', 'room', 'room_name',
            'weekday', 'weekday_display', 'start_time', 'end_time',
            'duration_hours', 'next_occurrence', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'duration_hours', 'next_occurrence'
        )


class LessonCreateSerializer(serializers.ModelSerializer):
    """
    Lesson creation serializer
    """
    class Meta:
        model = Lesson
        fields = ['group', 'room', 'weekday', 'start_time', 'end_time']
    
    def validate(self, attrs):
        """
        Validate lesson creation
        """
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError(
                "Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak"
            )
        
        # Check for conflicts
        room = attrs['room']
        weekday = attrs['weekday']
        start_time = attrs['start_time']
        end_time = attrs['end_time']
        
        conflicting_lessons = Lesson.objects.filter(
            room=room,
            weekday=weekday,
            is_active=True
        )
        
        for lesson in conflicting_lessons:
            if (start_time < lesson.end_time and end_time > lesson.start_time):
                raise serializers.ValidationError(
                    f"{room.name} xonasi {lesson.get_weekday_display()} kuni "
                    f"{lesson.start_time}-{lesson.end_time} vaqtida band"
                )
        
        return attrs


class CalendarOverrideSerializer(BaseModelSerializer):
    """
    Calendar override serializer
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    alternative_room_name = serializers.CharField(source='alternative_room.name', read_only=True)
    
    class Meta:
        model = CalendarOverride
        fields = [
            'id', 'date', 'group', 'group_name', 'room', 'room_name',
            'is_canceled', 'alternative_time', 'alternative_room',
            'alternative_room_name', 'note', 'notify_students',
            'notification_sent', 'is_active', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + ('notification_sent',)


class CalendarOverrideCreateSerializer(serializers.ModelSerializer):
    """
    Calendar override creation serializer
    """
    class Meta:
        model = CalendarOverride
        fields = [
            'date', 'group', 'room', 'is_canceled', 'alternative_time',
            'alternative_room', 'note', 'notify_students'
        ]
    
    def validate_date(self, value):
        """
        Validate override date
        """
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("O'tgan sanaga override qo'yib bo'lmaydi")
        return value
    
    def validate(self, attrs):
        """
        Validate calendar override
        """
        if not attrs.get('is_canceled'):
            if not attrs.get('alternative_time') and not attrs.get('alternative_room'):
                raise serializers.ValidationError(
                    "Agar dars bekor qilinmagan bo'lsa, alternativ vaqt yoki xona ko'rsatilishi kerak"
                )
        
        return attrs
