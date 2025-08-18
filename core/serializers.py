from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer with common fields and methods
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        abstract = True
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for nested representations
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'role')
        read_only_fields = fields