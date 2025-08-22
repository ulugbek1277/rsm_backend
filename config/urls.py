# Api/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# -----------------------------
# API Root: barcha app endpointlari
# -----------------------------
@api_view(['GET'])
def api_root(request):
    return Response({
        "accounts": request.build_absolute_uri('/api/accounts/'),
        "courses": request.build_absolute_uri('/api/courses/'),
        "rooms": request.build_absolute_uri('/api/rooms/'),
        "schedules": request.build_absolute_uri('/api/schedules/'),
        "groups": request.build_absolute_uri('/api/groups/'),
        "students": request.build_absolute_uri('/api/students/'),
        "payments": request.build_absolute_uri('/api/payments/'),
        "attendance": request.build_absolute_uri('/api/attendance/'),
        "messaging": request.build_absolute_uri('/api/messaging/'),
        "tasks": request.build_absolute_uri('/api/tasks/'),
        "settingshub": request.build_absolute_uri('/api/settingshub/'),
        "swagger": request.build_absolute_uri('/swagger/'),
        "redoc": request.build_absolute_uri('/redoc/'),
    })



from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

...

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('admin/', admin.site.urls),

    # API Root
    path('api/', api_root, name='api-root'),

    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/rooms/', include('rooms.urls')),
    path('api/schedules/', include('schedules.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/students/', include('students.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/settingshub/', include('settingshub.urls')),

    # API Schema va Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Media va static fayllar development da
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)