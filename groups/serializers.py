from rest_framework import serializers
from .models import Group, GroupStudent
from apps.core.serializers import BaseModelSerializer, UserBasicSerializer


class GroupStudentSerializer(BaseModelSerializer):
    """
    Group student serializer
    """
    student_info = UserBasicSerializer(source='student', read_only=True)
    is_currently_active = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = GroupStudent
        fields = [
            'id', 'group', 'student', 'student_info', 'joined_at',
            'left_at', 'notes', 'is_currently_active', 'duration_days',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'is_currently_active', 'duration_days'
        )


class GroupSerializer(BaseModelSerializer):
    """
    Group serializer
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    current_students_count = serializers.ReadOnlyField()
    available_spots = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()
    students = GroupStudentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'course', 'course_title', 'teacher', 'teacher_name',
            'status', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
            'room', 'room_name', 'max_students', 'description',
            'current_students_count', 'available_spots', 'is_full',
            'completion_percentage', 'students', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'current_students_count', 'available_spots', 'is_full', 'completion_percentage'
        )


class GroupCreateSerializer(serializers.ModelSerializer):
    """
    Group creation serializer
    """
    class Meta:
        model = Group
        fields = [
            'name', 'course', 'teacher', 'planned_start', 'planned_end',
            'room', 'max_students', 'description'
        ]
    
    def validate(self, attrs):
        """
        Validate group creation
        """
        if attrs['planned_start'] >= attrs['planned_end']:
            raise serializers.ValidationError(
                "Boshlanish sanasi tugash sanasidan oldin bo'lishi kerak"
            )
        
        # Check if teacher is available
        teacher = attrs['teacher']
        if teacher.role != teacher.TEACHER:
            raise serializers.ValidationError("Faqat o'qituvchi rolini tanlash mumkin")
        
        return attrs


class GroupListSerializer(serializers.ModelSerializer):
    """
    Simplified group serializer for lists
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    current_students_count = serializers.ReadOnlyField()
    available_spots = serializers.ReadOnlyField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'course_title', 'teacher_name', 'status',
            'planned_start', 'planned_end', 'current_students_count',
            'available_spots', 'max_students'
        ]


class GroupStudentCreateSerializer(serializers.ModelSerializer):
    """
    Group student creation serializer
    """
    class Meta:
        model = GroupStudent
        fields = ['group', 'student', 'joined_at', 'notes']
    
    def validate(self, attrs):
        """
        Validate group student creation
        """
        group = attrs['group']
        student = attrs['student']
        
        # Check if student role is correct
        if student.role != student.STUDENT:
            raise serializers.ValidationError("Faqat o'quvchi rolini tanlash mumkin")
        
        # Check if group is full
        if group.is_full:
            raise serializers.ValidationError(f"{group.name} guruhi to'liq")
        
        # Check if student is already in group
        if GroupStudent.objects.filter(
            group=group, student=student, is_active=True
        ).exists():
            raise serializers.ValidationError(
                "O'quvchi allaqachon ushbu guruhda"
            )
        
        return attrs