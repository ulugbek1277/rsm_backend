from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import Employee, Student

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'phone_number': '+998901234567',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'teacher'
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.phone_number, '+998901234567')
        self.assertEqual(user.role, 'teacher')
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            phone_number='+998901234568',
            first_name='Admin',
            last_name='User'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)


class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='User',
            role='teacher'
        )
        self.user.set_password('testpass123')
        self.user.save()

    def test_login(self):
        url = reverse('login')
        data = {
            'phone_number': '+998901234567',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login(self):
        url = reverse('login')
        data = {
            'phone_number': '+998901234567',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
