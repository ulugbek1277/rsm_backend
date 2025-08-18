from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceSessionViewSet, AttendanceRecordViewSet, AbsenceReasonViewSet

router = DefaultRouter()
router.register(r'absence-reasons', AbsenceReasonViewSet)
router.register(r'attendance-sessions', AttendanceSessionViewSet)
router.register(r'attendance-records', AttendanceRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]