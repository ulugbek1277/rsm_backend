from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, StudentEnrollmentViewSet, 
    StudentDocumentViewSet, StudentNoteViewSet
)

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'enrollments', StudentEnrollmentViewSet)
router.register(r'documents', StudentDocumentViewSet)
router.register(r'notes', StudentNoteViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
