from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet, DebtSnapshotViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'debt-snapshots', DebtSnapshotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
