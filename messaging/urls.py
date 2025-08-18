from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SmsTemplateViewSet, SmsLogViewSet, BroadcastViewSet, MessagingTasksViewSet

router = DefaultRouter()
router.register(r'sms-templates', SmsTemplateViewSet)
router.register(r'sms-logs', SmsLogViewSet)
router.register(r'broadcasts', BroadcastViewSet)
router.register(r'messaging-tasks', MessagingTasksViewSet, basename='messaging-tasks')

urlpatterns = [
    path('', include(router.urls)),
]