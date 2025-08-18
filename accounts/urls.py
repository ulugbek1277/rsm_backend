from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    UserViewSet,
    EmployeeProfileViewSet,
    StudentProfileViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'employee-profiles', EmployeeProfileViewSet)
router.register(r'student-profiles', StudentProfileViewSet)

urlpatterns = [
    # JWT Authentication
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management
    path('', include(router.urls)),
]