from rest_framework import serializers
from .models import Room, RoomBooking
from apps.core.serializers import BaseModelSerializer


class RoomSerializer(BaseModelSerializer):
    """
    Room serializer
    """
    class Meta:
        model = Room
        fields = [
            'id', 'name', 'capacity', 'location', 'equipment', 'notes',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class RoomListSerializer(serializers.ModelSerializer):
    """
    Simplified room serializer for lists
    """
    class Meta:
        model = Room
        fields = ['id', 'name', 'capacity', 'location', 'is_active']


class RoomBookingSerializer(BaseModelSerializer):
    """
    Room booking serializer
    """
    room_name = serializers.CharField(source='room.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    is_current = serializers.ReadOnlyField()
    
    class Meta:
        model = RoomBooking
        fields = [
            'id', 'room', 'room_name', 'date', 'start_time', 'end_time',
            'group', 'group_name', 'status', 'purpose', 'notes',
            'duration_hours', 'is_current', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'duration_hours', 'is_current'
        )


class RoomBookingCreateSerializer(serializers.ModelSerializer):
    """
    Room booking creation serializer
    """
    class Meta:
        model = RoomBooking
        fields = [
            'room', 'date', 'start_time', 'end_time',
            'group', 'purpose', 'notes'
        ]
    
    def validate(self, attrs):
        """
        Validate booking constraints
        """
        room = attrs['room']
        date = attrs['date']
        start_time = attrs['start_time']
        end_time = attrs['end_time']
        
        if start_time >= end_time:
            raise serializers.ValidationError(
                "Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak"
            )
        
        if not room.is_available(date, start_time, end_time):
            raise serializers.ValidationError(
                f"{room.name} xonasi {date} sanasida "
                f"{start_time}-{end_time} vaqtida band"
            )
        
        return attrs


class RoomAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for checking room availability
    """
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
