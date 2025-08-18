from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, StudentEnrollment, StudentDocument, StudentNote
from apps.courses.serializers import CourseSerializer

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    active_enrollments_count = serializers.SerializerMethodField()
    total_payments = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'user', 'first_name', 'last_name', 'middle_name', 'full_name',
            'birth_date', 'age', 'gender', 'phone', 'email', 'user_email',
            'region', 'district', 'address', 'education_level', 'school_name',
            'parent_name', 'parent_phone', 'status', 'enrollment_date',
            'notes', 'photo', 'total_debt', 'last_payment_date',
            'active_enrollments_count', 'total_payments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['enrollment_date', 'total_debt', 'last_payment_date']

    def get_active_enrollments_count(self, obj):
        return obj.get_active_enrollments().count()

    def get_total_payments(self, obj):
        return obj.get_total_payments()

    def create(self, validated_data):
        # Create user if not provided
        if 'user' not in validated_data:
            user_data = {
                'username': validated_data['phone'],
                'email': validated_data.get('email', ''),
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'role': 'student',
                'phone': validated_data['phone'],
            }
            user = User.objects.create_user(**user_data)
            validated_data['user'] = user
        
        return super().create(validated_data)


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    active_enrollments_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'phone', 'age', 'status', 
            'enrollment_date', 'total_debt', 'active_enrollments_count'
        ]

    def get_active_enrollments_count(self, obj):
        return obj.get_active_enrollments().count()


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = StudentEnrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_id', 'course_title',
            'enrollment_date', 'start_date', 'end_date', 'status',
            'progress_percentage', 'grade', 'notes', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        # Check if student is already enrolled in this course
        if StudentEnrollment.objects.filter(
            student=data['student'], 
            course_id=data['course_id'],
            status='active'
        ).exists():
            raise serializers.ValidationError(
                "Talaba bu kursga allaqachon ro'yxatdan o'tgan"
            )
        return data


class StudentDocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = StudentDocument
        fields = [
            'id', 'student', 'student_name', 'document_type', 'title',
            'file', 'description', 'created_at', 'updated_at'
        ]


class StudentNoteSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = StudentNote
        fields = [
            'id', 'student', 'student_name', 'author', 'author_name',
            'note_type', 'title', 'content', 'is_important',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class StudentDetailSerializer(StudentSerializer):
    enrollments = StudentEnrollmentSerializer(many=True, read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    notes = StudentNoteSerializer(many=True, read_only=True)

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ['enrollments', 'documents', 'notes']
