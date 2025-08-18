from rest_framework import serializers
from .models import Task, TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'comment', 'author', 'author_name', 'created_at']
        read_only_fields = ['author']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'assigned_to', 'assigned_to_name', 'assigned_by', 'assigned_by_name',
            'due_date', 'completed_at', 'attachment', 'comments', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['assigned_by', 'completed_at']

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'assigned_to', 'due_date', 'attachment']

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)
