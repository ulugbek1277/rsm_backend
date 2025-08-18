from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GlobalSettingsViewSet, UserSettingsViewSet, 
    SettingsCategoryViewSet, SettingsBackupViewSet
)

router = DefaultRouter()
router.register(r'global', GlobalSettingsViewSet)
router.register(r'user', UserSettingsViewSet)
router.register(r'categories', SettingsCategoryViewSet)
router.register(r'backups', SettingsBackupViewSet)

urlpatterns = [
    path('api/settings/', include(router.urls)),
]
