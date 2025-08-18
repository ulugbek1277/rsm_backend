from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.courses.models import Course

User = get_user_model()


class CourseModelTest(TestCase):
    def setUp(self):
        self.course_data = {
            'title': 'Python dasturlash',
            'description': 'Python dasturlash kursi',
            'price': 500000,
            'duration_months': 6
        }

    def test_create_course(self):
        course = Course.objects.create(**self.course_data)
        self.assertEqual(course.title, 'Python dasturlash')
        self.assertEqual(course.slug, 'python-dasturlash')
        self.assertTrue(course.is_active)

    def test_course_str(self):
        course = Course.objects.create(**self.course_data)
        self.assertEqual(str(course), 'Python dasturlash')


class CourseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='User',
            role='administrator'
        )
        self.client.force_authenticate(user=self.user)
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=300000,
            duration_months=3
        )

    def test_get_courses(self):
        url = '/api/courses/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_course(self):
        url = '/api/courses/'
        data = {
            'title': 'New Course',
            'description': 'New Description',
            'price': 400000,
            'duration_months': 4
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)