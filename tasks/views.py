from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Task, TaskComment
from .serializers import TaskSerializer, TaskCreateSerializer, TaskCommentSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('assigned_to', 'assigned_by').prefetch_related('comments')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'assigned_to']

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Faqat o'z vazifalarini yoki o'zi tayinlagan vazifalarni ko'rish
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(assigned_by=user)
            )
        
        return queryset

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Foydalanuvchining o'z vazifalari"""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def assigned_by_me(self, request):
        """Foydalanuvchi tayinlagan vazifalar"""
        tasks = self.get_queryset().filter(assigned_by=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Vazifaga izoh qo'shish"""
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Vazifa holatini yangilash"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Noto\'g\'ri holat'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
