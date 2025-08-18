from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.courses.urls')),
    path('api/', include('apps.rooms.urls')),
    path('api/', include('apps.schedules.urls')),
    path('api/', include('apps.groups.urls')),
    path('api/', include('apps.students.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.attendance.urls')),
    path('api/', include('apps.exams.urls')),
    path('api/', include('apps.messaging.urls')),
    path('api/', include('apps.tasks.urls')),
    path('api/', include('apps.settingshub.urls')),
    
    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
