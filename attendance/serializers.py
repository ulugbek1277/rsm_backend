from rest_framework import serializers
from .models import AttendanceSession, AttendanceRecord, AbsenceReason
from apps.core.serializers import BaseModelSerializer, UserBasicSerializer


class AbsenceReasonSerializer(BaseModelSerializer):
    """
    Absence reason serializer
    """
    class Meta:
        model = AbsenceReason
        fields = [
            'id', 'name', 'description', 'requires_notification',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields


class AttendanceRecordSerializer(BaseModelSerializer):
    """
    Attendance record serializer
    """
    student_info = UserBasicSerializer(source='student', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    absence_reason_name = serializers.CharField(source='absence_reason.name', read_only=True)
    is_absent = serializers.ReadOnlyField()
    is_present = serializers.ReadOnlyField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'student', 'student_info', 'status',
            'status_display', 'absence_reason', 'absence_reason_name',
            'comment', 'notification_sent', 'is_absent', 'is_present',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'notification_sent', 'is_absent', 'is_present'
        )


class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """
    Attendance record creation serializer
    """
    class Meta:
        model = AttendanceRecord
        fields = ['session', 'student', 'status', 'absence_reason', 'comment']
    
    def validate(self, attrs):
        """
        Validate attendance record
        """
        status = attrs['status']
        absence_reason = attrs.get('absence_reason')
        
        # Absence reason is required for absent statuses
        if status in ['absent_excused', 'absent_unexcused'] and not absence_reason:
            raise serializers.ValidationError(
                "Yo'qlik uchun sabab ko'rsatilishi kerak"
            )
        
        # Absence reason should not be set for present/late
        if status in ['present', 'late'] and absence_reason:
            raise serializers.ValidationError(
                "Hozir yoki kech kelgan holat uchun sabab kerak emas"
            )
        
        return attrs


class AttendanceSessionSerializer(BaseModelSerializer):
    """
    Attendance session serializer
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    taken_by_name = serializers.CharField(source='taken_by.get_full_name', read_only=True)
    lesson_info = serializers.SerializerMethodField()
    total_students = serializers.ReadOnlyField()
    present_count = serializers.ReadOnlyField()
    absent_count = serializers.ReadOnlyField()
    late_count = serializers.ReadOnlyField()
    attendance_percentage = serializers.ReadOnlyField()
    records = AttendanceRecordSerializer(many=True, read_only=True)
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'group', 'group_name', 'date', 'taken_by', 'taken_by_name',
            'lesson', 'lesson_info', 'notes', 'total_students', 'present_count',
            'absent_count', 'late_count', 'attendance_percentage', 'records',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'total_students', 'present_count', 'absent_count', 'late_count',
            'attendance_percentage'
        )
    
    def get_lesson_info(self, obj):
        if obj.lesson:
            return {
                'id': obj.lesson.id,
                'weekday': obj.lesson.get_weekday_display(),
                'time': f"{obj.lesson.start_time} - {obj.lesson.end_time}",
                'room': obj.lesson.room.name
            }
        return None


class AttendanceSessionCreateSerializer(serializers.ModelSerializer):
    """
    Attendance session creation serializer
    """
    class Meta:
        model = AttendanceSession
        fields = ['group', 'date', 'lesson', 'notes']
    
    def validate(self, attrs):
        """
        Validate attendance session
        """
        group = attrs['group']
        date = attrs['date']
        lesson = attrs.get('lesson')
        
        # Check if session already exists
        existing_session = AttendanceSession.objects.filter(
            group=group,
            date=date,
            lesson=lesson,
            is_active=True
        ).exists()
        
        if existing_session:
            raise serializers.ValidationError(
                "Bu guruh uchun ushbu sanada davomat allaqachon olingan"
            )
        
        return attrs


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for bulk attendance taking
    """
    session_id = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_records(self, value):
        """
        Validate attendance records format
        """
        required_fields = ['student_id', 'status']
        
        for record in value:
            for field in required_fields:
                if field not in record:
                    raise serializers.ValidationError(
                        f"'{field}' maydoni har bir record uchun kerak"
                    )
            
            # Validate status
            valid_statuses = ['present', 'late', 'absent_excused', 'absent_unexcused']
            if record['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    f"Noto'g'ri status: {record['status']}"
                )
        
        return value