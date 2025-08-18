from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, EmployeeProfile, StudentProfile
from apps.core.serializers import BaseModelSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with user info
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user info to token response
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'full_name': self.user.get_full_name(),
                'role': self.user.role,
                'phone': self.user.phone,
                'is_active': self.user.is_active,
            }
        })
        
        return data


class EmployeeProfileSerializer(BaseModelSerializer):
    """
    Serializer for Employee Profile
    """
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'position', 'passport_series', 'passport_number',
            'passport_issued_by', 'passport_issued_date', 'address',
            'birth_date', 'hire_date', 'salary', 'emergency_contact_name',
            'emergency_contact_phone', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


class StudentProfileSerializer(BaseModelSerializer):
    """
    Serializer for Student Profile
    """
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'parent_name', 'parent_phone', 'address', 'birth_date',
            'avatar', 'school_name', 'school_grade', 'medical_info',
            'notes', 'age', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'age', 'created_at', 'updated_at')


class UserSerializer(BaseModelSerializer):
    """
    Main User serializer
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    employee_profile = EmployeeProfileSerializer(read_only=True)
    student_profile = StudentProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'role', 'is_active', 'date_joined',
            'employee_profile', 'student_profile', 'password'
        ]
        read_only_fields = ('id', 'date_joined', 'full_name')
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Parollar mos kelmaydi")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Yangi parollar mos kelmaydi")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    employee_profile = EmployeeProfileSerializer(required=False)
    student_profile = StudentProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'employee_profile', 'student_profile'
        ]
    
    def update(self, instance, validated_data):
        employee_profile_data = validated_data.pop('employee_profile', None)
        student_profile_data = validated_data.pop('student_profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update employee profile
        if employee_profile_data and hasattr(instance, 'employee_profile'):
            employee_profile = instance.employee_profile
            for attr, value in employee_profile_data.items():
                setattr(employee_profile, attr, value)
            employee_profile.save()
        
        # Update student profile
        if student_profile_data and hasattr(instance, 'student_profile'):
            student_profile = instance.student_profile
            for attr, value in student_profile_data.items():
                setattr(student_profile, attr, value)
            student_profile.save()
        
        return instance