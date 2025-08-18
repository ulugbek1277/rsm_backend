from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, RoomBookingViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'room-bookings', RoomBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
