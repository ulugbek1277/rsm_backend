from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemSettingsViewSet, NotificationSettingsViewSet, PaymentSettingsViewSet

router = DefaultRouter()
router.register(r'system-settings', SystemSettingsViewSet)
router.register(r'notification-settings', NotificationSettingsViewSet)
router.register(r'payment-settings', PaymentSettingsViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
