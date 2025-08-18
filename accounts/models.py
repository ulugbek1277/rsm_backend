from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.core.utils import validate_phone_number


class User(AbstractUser, SoftDeleteModel, TimeStampedModel):
    """
    Custom User model with role-based access
    """
    SUPER_ADMIN = 'superadmin'
    ADMINISTRATOR = 'administrator'
    TEACHER = 'teacher'
    ACCOUNTANT = 'accountant'
    STUDENT = 'student'
    
    ROLE_CHOICES = [
        (SUPER_ADMIN, 'Super Admin'),
        (ADMINISTRATOR, 'Administrator'),
        (TEACHER, 'Teacher'),
        (ACCOUNTANT, 'Accountant'),
        (STUDENT, 'Student'),
    ]
    
    phone_validator = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message="Telefon raqam formati: +998XXXXXXXXX"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT
    )
    phone = models.CharField(
        max_length=13,
        unique=True,
        validators=[phone_validator],
        help_text="Format: +998XXXXXXXXX"
    )
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_superadmin(self):
        return self.role == self.SUPER_ADMIN
    
    @property
    def is_administrator(self):
        return self.role == self.ADMINISTRATOR
    
    @property
    def is_teacher(self):
        return self.role == self.TEACHER
    
    @property
    def is_accountant(self):
        return self.role == self.ACCOUNTANT
    
    @property
    def is_student(self):
        return self.role == self.STUDENT
    
    @property
    def is_staff_member(self):
        return self.role in [self.SUPER_ADMIN, self.ADMINISTRATOR, self.TEACHER, self.ACCOUNTANT]


class EmployeeProfile(TimeStampedModel, SoftDeleteModel):
    """
    Profile for staff members (SuperAdmin, Administrator, Teacher, Accountant)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    position = models.CharField(max_length=100, blank=True)
    passport_series = models.CharField(max_length=2, blank=True)
    passport_number = models.CharField(max_length=7, blank=True)
    passport_issued_by = models.CharField(max_length=200, blank=True)
    passport_issued_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)
    
    class Meta:
        db_table = 'accounts_employee_profile'
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class StudentProfile(TimeStampedModel, SoftDeleteModel):
    """
    Profile for students
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(
        max_length=13,
        validators=[RegexValidator(
            regex=r'^\+998[0-9]{9}$',
            message="Telefon raqam formati: +998XXXXXXXXX"
        )]
    )
    address = models.TextField()
    birth_date = models.DateField()
    avatar = models.ImageField(
        upload_to='students/avatars/',
        null=True,
        blank=True
    )
    school_name = models.CharField(max_length=200, blank=True)
    school_grade = models.CharField(max_length=10, blank=True)
    medical_info = models.TextField(blank=True, help_text="Tibbiy ma'lumotlar")
    notes = models.TextField(blank=True, help_text="Qo'shimcha eslatmalar")
    
    class Meta:
        db_table = 'accounts_student_profile'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.parent_name}"
    
    @property
    def age(self):
        from datetime import date
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
