from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.attendance.models import AttendanceSession, AttendanceRecord
from apps.groups.models import Group
from apps.courses.models import Course
from apps.accounts.models import Student

User = get_user_model()


class AttendanceTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Teacher',
            last_name='User',
            role='teacher'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            price=300000,
            duration_months=3
        )
        
        self.group = Group.objects.create(
            name='Test Group',
            course=self.course,
            teacher=self.teacher,
            start_date=timezone.now().date()
        )
        
        self.student_user = User.objects.create_user(
            phone_number='+998901234568',
            first_name='Student',
            last_name='User',
            role='student'
        )
        
        self.student = Student.objects.create(
            user=self.student_user,
            parent_name='Parent Name',
            parent_phone='+998901234569'
        )
        
        self.group.students.add(self.student)

    def test_create_attendance_session(self):
        session = AttendanceSession.objects.create(
            group=self.group,
            teacher=self.teacher,
            date=timezone.now().date(),
            topic='Test Topic'
        )
        
        self.assertEqual(session.group, self.group)
        self.assertEqual(session.teacher, self.teacher)
        self.assertEqual(session.status, 'active')

    def test_attendance_record(self):
        session = AttendanceSession.objects.create(
            group=self.group,
            teacher=self.teacher,
            date=timezone.now().date(),
            topic='Test Topic'
        )
        
        record = AttendanceRecord.objects.create(
            session=session,
            student=self.student,
            status='present'
        )
        
        self.assertEqual(record.session, session)
        self.assertEqual(record.student, self.student)
        self.assertEqual(record.status, 'present')
