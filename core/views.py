from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with common functionality
    """
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_by field"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by field"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active objects"""
        queryset = self.get_queryset().filter(is_active=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        """Soft delete object"""
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        return Response({'status': 'Object deactivated'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore soft deleted object"""
        obj = self.get_object()
        obj.is_active = True
        obj.save()
        return Response({'status': 'Object restored'}, status=status.HTTP_200_OK)