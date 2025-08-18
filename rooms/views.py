from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Room, RoomBooking
from .serializers import (
    RoomSerializer, RoomListSerializer, RoomBookingSerializer,
    RoomBookingCreateSerializer, RoomAvailabilitySerializer
)
from apps.core.permissions import IsAdminOrReadOnly
from apps.core.views import BaseModelViewSet


class RoomViewSet(BaseModelViewSet):
    """
    ViewSet for Room management
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['is_active', 'capacity']
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'capacity', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RoomListSerializer
        return RoomSerializer
    
    @action(detail=True, methods=['post'])
    def check_availability(self, request, pk=None):
        """
        Check room availability for given time slot
        """
        room = self.get_object()
        serializer = RoomAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        
        is_available = room.is_available(date, start_time, end_time)
        
        return Response({
            'available': is_available,
            'room': room.name,
            'date': date,
            'time_slot': f"{start_time} - {end_time}"
        })
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """
        Get all bookings for this room
        """
        room = self.get_object()
        bookings = room.bookings.filter(is_active=True).order_by('date', 'start_time')
        
        # Filter by date range if provided
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            bookings = bookings.filter(date__gte=date_from)
        if date_to:
            bookings = bookings.filter(date__lte=date_to)
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = RoomBookingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RoomBookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_now(self, request):
        """
        Get rooms available right now
        """
        now = timezone.now()
        current_time = now.time()
        current_date = now.date()
        
        available_rooms = []
        for room in self.get_queryset().filter(is_active=True):
            # Check if room has any current bookings
            current_bookings = room.bookings.filter(
                date=current_date,
                start_time__lte=current_time,
                end_time__gt=current_time,
                status__in=['confirmed', 'in_progress']
            )
            
            if not current_bookings.exists():
                available_rooms.append(room)
        
        serializer = RoomListSerializer(available_rooms, many=True)
        return Response(serializer.data)


class RoomBookingViewSet(BaseModelViewSet):
    """
    ViewSet for Room Booking management
    """
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['room', 'date', 'status', 'group']
    search_fields = ['room__name', 'group__name', 'purpose']
    ordering_fields = ['date', 'start_time', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RoomBookingCreateSerializer
        return RoomBookingSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's bookings
        """
        today = timezone.now().date()
        bookings = self.get_queryset().filter(date=today, is_active=True)
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming bookings (next 7 days)
        """
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        bookings = self.get_queryset().filter(
            date__range=[today, next_week],
            is_active=True
        ).order_by('date', 'start_time')
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm booking
        """
        booking = self.get_object()
        booking.status = 'confirmed'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel booking
        """
        booking = self.get_object()
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
