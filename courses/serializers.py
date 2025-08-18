from rest_framework import serializers
from .models import Course
from apps.core.serializers import BaseModelSerializer


class CourseSerializer(BaseModelSerializer):
    """
    Course serializer
    """
    total_price = serializers.ReadOnlyField()
    active_groups_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'price_monthly',
            'duration_months', 'max_students', 'prerequisites',
            'objectives', 'syllabus', 'certificate_template',
            'total_price', 'active_groups_count', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            'slug', 'total_price', 'active_groups_count'
        )


class CourseCreateSerializer(serializers.ModelSerializer):
    """
    Course creation serializer
    """
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'price_monthly', 'duration_months',
            'max_students', 'prerequisites', 'objectives', 'syllabus',
            'certificate_template'
        ]


class CourseListSerializer(serializers.ModelSerializer):
    """
    Simplified course serializer for lists
    """
    total_price = serializers.ReadOnlyField()
    active_groups_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'price_monthly', 'duration_months',
            'max_students', 'total_price', 'active_groups_count', 'is_active'
        ]