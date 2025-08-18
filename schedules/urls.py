from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, CalendarOverrideViewSet

router = DefaultRouter()
router.register(r'lessons', LessonViewSet)
router.register(r'calendar-overrides', CalendarOverrideViewSet)

urlpatterns = [
    path('', include(router.urls)),
]