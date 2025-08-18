"""
Sample ma'lumotlar yaratish skripti
Bu skript test va demo uchun sample ma'lumotlar yaratadi
"""

import os
import sys
import django
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

# Django sozlamalarini yuklash
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.courses.models import Course
from apps.rooms.models import Room
from apps.groups.models import Group
from apps.accounts.models import Student, Employee
from apps.schedules.models import Lesson
from apps.payments.models import Invoice
from apps.settings.models import SystemSettings, NotificationSettings, PaymentSettings

User = get_user_model()

def create_sample_data():
    print("Sample ma'lumotlar yaratilmoqda...")
    
    # 1. Superuser yaratish
    if not User.objects.filter(is_superuser=True).exists():
        superuser = User.objects.create_superuser(
            phone_number='+998901234567',
            first_name='Super',
            last_name='Admin',
            password='admin123'
        )
        print(f"✅ Superuser yaratildi: {superuser.phone_number}")
    
    # 2. Xodimlar yaratish
    employees_data = [
        {
            'phone_number': '+998901234568',
            'first_name': 'Aziz',
            'last_name': 'Karimov',
            'role': 'administrator',
            'password': 'admin123'
        },
        {
            'phone_number': '+998901234569',
            'first_name': 'Malika',
            'last_name': 'Tosheva',
            'role': 'teacher',
            'password': 'teacher123'
        },
        {
            'phone_number': '+998901234570',
            'first_name': 'Bobur',
            'last_name': 'Alimov',
            'role': 'teacher',
            'password': 'teacher123'
        },
        {
            'phone_number': '+998901234571',
            'first_name': 'Nigora',
            'last_name': 'Rahimova',
            'role': 'accountant',
            'password': 'accountant123'
        }
    ]
    
    created_employees = []
    for emp_data in employees_data:
        if not User.objects.filter(phone_number=emp_data['phone_number']).exists():
            password = emp_data.pop('password')
            user = User.objects.create_user(**emp_data)
            user.set_password(password)
            user.save()
            
            Employee.objects.create(
                user=user,
                position=emp_data['role'].title(),
                hire_date=date.today() - timedelta(days=30)
            )
            created_employees.append(user)
            print(f"✅ Xodim yaratildi: {user.get_full_name()} ({user.role})")
    
    # 3. Kurslar yaratish
    courses_data = [
        {
            'title': 'Python dasturlash',
            'description': 'Python dasturlash tili asoslari va web development',
            'price': Decimal('500000'),
            'duration_months': 6
        },
        {
            'title': 'Frontend Development',
            'description': 'HTML, CSS, JavaScript va React.js',
            'price': Decimal('450000'),
            'duration_months': 5
        },
        {
            'title': 'Grafik dizayn',
            'description': 'Adobe Photoshop, Illustrator va Figma',
            'price': Decimal('400000'),
            'duration_months': 4
        },
        {
            'title': 'Ingliz tili',
            'description': 'Umumiy ingliz tili kursi',
            'price': Decimal('300000'),
            'duration_months': 8
        }
    ]
    
    created_courses = []
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults=course_data
        )
        if created:
            created_courses.append(course)
            print(f"✅ Kurs yaratildi: {course.title}")
    
    # 4. Xonalar yaratish
    rooms_data = [
        {'name': 'A-101', 'capacity': 15, 'has_projector': True},
        {'name': 'A-102', 'capacity': 12, 'has_projector': True},
        {'name': 'B-201', 'capacity': 20, 'has_projector': False},
        {'name': 'B-202', 'capacity': 18, 'has_projector': True},
    ]
    
    created_rooms = []
    for room_data in rooms_data:
        room, created = Room.objects.get_or_create(
            name=room_data['name'],
            defaults=room_data
        )
        if created:
            created_rooms.append(room)
            print(f"✅ Xona yaratildi: {room.name}")
    
    # 5. O'quvchilar yaratish
    students_data = [
        {
            'phone_number': '+998901234580',
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'parent_name': 'Karim Valiyev',
            'parent_phone': '+998901234590'
        },
        {
            'phone_number': '+998901234581',
            'first_name': 'Zarina',
            'last_name': 'Nazarova',
            'parent_name': 'Dilshod Nazarov',
            'parent_phone': '+998901234591'
        },
        {
            'phone_number': '+998901234582',
            'first_name': 'Jasur',
            'last_name': 'Tursunov',
            'parent_name': 'Akmal Tursunov',
            'parent_phone': '+998901234592'
        },
        {
            'phone_number': '+998901234583',
            'first_name': 'Madina',
            'last_name': 'Karimova',
            'parent_name': 'Sevara Karimova',
            'parent_phone': '+998901234593'
        }
    ]
    
    created_students = []
    for student_data in students_data:
        if not User.objects.filter(phone_number=student_data['phone_number']).exists():
            parent_name = student_data.pop('parent_name')
            parent_phone = student_data.pop('parent_phone')
            
            user = User.objects.create_user(
                role='student',
                password='student123',
                **student_data
            )
            
            student = Student.objects.create(
                user=user,
                parent_name=parent_name,
                parent_phone=parent_phone,
                birth_date=date(2005, 1, 1)
            )
            created_students.append(student)
            print(f"✅ O'quvchi yaratildi: {user.get_full_name()}")
    
    # 6. Guruhlar yaratish
    if created_courses and created_employees and created_rooms:
        teachers = [emp for emp in created_employees if emp.role == 'teacher']
        
        if teachers:
            groups_data = [
                {
                    'name': 'Python-01',
                    'course': created_courses[0],
                    'teacher': teachers[0],
                    'room': created_rooms[0],
                    'start_date': date.today() + timedelta(days=7)
                },
                {
                    'name': 'Frontend-01',
                    'course': created_courses[1] if len(created_courses) > 1 else created_courses[0],
                    'teacher': teachers[1] if len(teachers) > 1 else teachers[0],
                    'room': created_rooms[1] if len(created_rooms) > 1 else created_rooms[0],
                    'start_date': date.today() + timedelta(days=14)
                }
            ]
            
            for group_data in groups_data:
                group, created = Group.objects.get_or_create(
                    name=group_data['name'],
                    defaults=group_data
                )
                if created:
                    # Guruhga o'quvchilar qo'shish
                    if created_students:
                        for student in created_students[:2]:  # Har guruhga 2 tadan o'quvchi
                            group.students.add(student)
                    print(f"✅ Guruh yaratildi: {group.name}")
    
    # 7. Sozlamalar yaratish
    settings_data = [
        {'key': 'site_name', 'value': 'EduMaster CRM', 'description': 'Sayt nomi'},
        {'key': 'sms_enabled', 'value': 'true', 'setting_type': 'boolean', 'description': 'SMS yoqilgan'},
        {'key': 'max_students_per_group', 'value': '15', 'setting_type': 'number', 'description': 'Guruhdagi maksimal o\'quvchilar soni'},
    ]
    
    for setting_data in settings_data:
        setting, created = SystemSettings.objects.get_or_create(
            key=setting_data['key'],
            defaults=setting_data
        )
        if created:
            print(f"✅ Sozlama yaratildi: {setting.key}")
    
    # 8. Xabarnoma sozlamalari
    if not NotificationSettings.objects.exists():
        NotificationSettings.objects.create()
        print("✅ Xabarnoma sozlamalari yaratildi")
    
    # 9. To'lov sozlamalari
    if not PaymentSettings.objects.exists():
        PaymentSettings.objects.create()
        print("✅ To'lov sozlamalari yaratildi")
    
    print("\n🎉 Sample ma'lumotlar muvaffaqiyatli yaratildi!")
    print("\nKirish ma'lumotlari:")
    print("Superuser: +998901234567 / admin123")
    print("Administrator: +998901234568 / admin123")
    print("Teacher: +998901234569 / teacher123")
    print("Accountant: +998901234571 / accountant123")
    print("Student: +998901234580 / student123")

if __name__ == '__main__':
    create_sample_data()
