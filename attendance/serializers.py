from rest_framework import serializers
from .models import AttendanceSession, AttendanceRecord, AbsenceReason
from core.serializers import BaseModelSerializer, UserBasicSerializer

# -----------------------------
# AbsenceReason Serializer
# -----------------------------
class AbsenceReasonSerializer(BaseModelSerializer):
    class Meta:
        model = AbsenceReason
        fields = ['id', 'title', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = BaseModelSerializer.Meta.read_only_fields

# -----------------------------
# AttendanceRecord Serializer
# -----------------------------
class AttendanceRecordSerializer(BaseModelSerializer):
    student_info = UserBasicSerializer(source='student', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reason_title = serializers.CharField(source='reason.title', read_only=True)
    is_absent = serializers.ReadOnlyField()
    is_present = serializers.ReadOnlyField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'student', 'student_info', 'status',
            'status_display', 'reason', 'reason_title',
            'comment', 'notification_sent', 'is_absent', 'is_present',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'notification_sent', 'is_absent', 'is_present'
        )

# -----------------------------
# AttendanceRecord Create Serializer
# -----------------------------
class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ['session', 'student', 'status', 'reason', 'comment']
    
    def validate(self, attrs):
        status = attrs['status']
        reason = attrs.get('reason')
        
        if status in ['absent_excused', 'absent_unexcused'] and not reason:
            raise serializers.ValidationError("Yo'qlik uchun sabab ko'rsatilishi kerak")
        if status in ['present', 'late'] and reason:
            raise serializers.ValidationError("Hozir yoki kech kelgan holat uchun sabab kerak emas")
        return attrs

# -----------------------------
# AttendanceSession Serializer
# -----------------------------
class AttendanceSessionSerializer(BaseModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
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
            'id', 'group', 'group_name', 'date', 'teacher', 'teacher_name',
            'lesson', 'lesson_info', 'notes', 'total_students', 'present_count',
            'absent_count', 'late_count', 'attendance_percentage', 'records',
            'is_active', 'created_at', 'updated_at'
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

# -----------------------------
# AttendanceSession Create Serializer
# -----------------------------
class AttendanceSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = ['group', 'date', 'lesson', 'notes']
    
    def validate(self, attrs):
        group = attrs['group']
        date = attrs['date']
        lesson = attrs.get('lesson')
        if AttendanceSession.objects.filter(group=group, date=date, lesson=lesson, is_active=True).exists():
            raise serializers.ValidationError("Bu guruh uchun ushbu sanada davomat allaqachon olingan")
        return attrs

# -----------------------------
# BulkAttendance Serializer
# -----------------------------
class BulkAttendanceSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )
    
    def validate_records(self, value):
        required_fields = ['student_id', 'status']
        valid_statuses = ['present', 'late', 'absent_excused', 'absent_unexcused']
        
        for record in value:
            for field in required_fields:
                if field not in record:
                    raise serializers.ValidationError(f"'{field}' maydoni har bir record uchun kerak")
            if record['status'] not in valid_statuses:
                raise serializers.ValidationError(f"Noto'g'ri status: {record['status']}")
        return value