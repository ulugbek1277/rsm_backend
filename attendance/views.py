from rest_framework import viewsets
from .models import AttendanceSession, AttendanceRecord, AbsenceReason
from .serializers import AttendanceSessionSerializer, AttendanceRecordSerializer, AbsenceReasonSerializer

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer

class AbsenceReasonViewSet(viewsets.ModelViewSet):
    queryset = AbsenceReason.objects.all()
    serializer_class = AbsenceReasonSerializer