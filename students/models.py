from django.db import models
from django.core.validators import RegexValidator
from core.models import BaseModel
from accounts.models import User
from courses.models import Course

class Student(BaseModel):
    """Talaba haqidagi batafsil ma'lumotlar"""

    GENDER_CHOICES = [
        ('male', 'Erkak'),
        ('female', 'Ayol'),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ('school', 'Maktab'),
        ('college', 'Kollej'),
        ('university', 'Universitet'),
        ('graduated', 'Bitirgan'),
        ('working', 'Ishlaydigan'),
    ]

    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('inactive', 'Nofaol'),
        ('graduated', 'Bitirgan'),
        ('dropped', 'Tashlab ketgan'),
    ]

    # ⚠ related_name ni noyob qildim
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_main_profile'
    )

    # Personal Information
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Otasining ismi")
    birth_date = models.DateField(verbose_name="Tug'ilgan sana")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Jinsi")

    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message="Telefon raqami +998XXXXXXXXX formatida bo'lishi kerak"
    )
    phone = models.CharField(validators=[phone_regex], max_length=13, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Address
    region = models.CharField(max_length=100, verbose_name="Viloyat")
    district = models.CharField(max_length=100, verbose_name="Tuman")
    address = models.TextField(verbose_name="Manzil")

    # Education
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name="Ta'lim darajasi"
    )
    school_name = models.CharField(max_length=200, blank=True, verbose_name="Maktab/Universitet nomi")

    # Parent Information
    parent_name = models.CharField(max_length=200, verbose_name="Ota-ona ismi")
    parent_phone = models.CharField(validators=[phone_regex], max_length=13, verbose_name="Ota-ona telefoni")

    # Student Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Holati")
    enrollment_date = models.DateField(auto_now_add=True, verbose_name="Ro'yxatga olingan sana")

    # Additional Information
    notes = models.TextField(blank=True, verbose_name="Qo'shimcha ma'lumotlar")

    # ⚠ Pillow o‘rnatilishi shart
    photo = models.ImageField(upload_to='students/photos/', blank=True, verbose_name="Rasm")

    # Tracking
    total_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Umumiy qarz")
    last_payment_date = models.DateField(null=True, blank=True, verbose_name="Oxirgi to'lov sanasi")

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def get_active_enrollments(self):
        return self.enrollments.filter(status='active')

    def get_total_payments(self):
        from payments.models import Payment
        return Payment.objects.filter(student=self).aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class StudentEnrollment(BaseModel):
    """Talabaning kursga yozilishi"""

    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('completed', 'Tugallangan'),
        ('dropped', 'Tashlab ketgan'),
        ('suspended', 'Toxtatilgan'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name="Talaba"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='student_enrollments',
        verbose_name="Kurs"
    )

    enrollment_date = models.DateField(auto_now_add=True, verbose_name="Ro'yxatga olingan sana")
    start_date = models.DateField(verbose_name="Boshlangan sana")
    end_date = models.DateField(null=True, blank=True, verbose_name="Tugagan sana")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Holati")

    # Progress tracking
    progress_percentage = models.IntegerField(default=0, verbose_name="Jarayon foizi")
    grade = models.CharField(max_length=5, blank=True, verbose_name="Baho")

    notes = models.TextField(blank=True, verbose_name="Izohlar")

    class Meta:
        verbose_name = "Talaba ro'yxati"
        verbose_name_plural = "Talabalar ro'yxati"
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student.full_name} - {self.course.title}"


class StudentDocument(BaseModel):
    """Talaba hujjatlari"""

    DOCUMENT_TYPES = [
        ('passport', 'Pasport'),
        ('birth_certificate', "Tug'ilganlik haqidagi guvohnoma"),
        ('diploma', 'Diplom'),
        ('certificate', 'Sertifikat'),
        ('photo', 'Rasm'),
        ('other', 'Boshqa'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Talaba"
    )

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Hujjat turi")
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    file = models.FileField(upload_to='students/documents/', verbose_name="Fayl")
    description = models.TextField(blank=True, verbose_name="Tavsif")

    class Meta:
        verbose_name = "Talaba hujjati"
        verbose_name_plural = "Talaba hujjatlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.title}"


class StudentNote(BaseModel):
    """Talaba haqida eslatmalar"""

    NOTE_TYPES = [
        ('general', 'Umumiy'),
        ('academic', 'Akademik'),
        ('behavioral', 'Xulq-atvor'),
        ('attendance', 'Davomat'),
        ('payment', "To'lov"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='student_notes_all',
        verbose_name="Talaba"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_notes_authored',
        verbose_name="Muallif"
    )

    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general', verbose_name="Eslatma turi")
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    content = models.TextField(verbose_name="Mazmun")
    is_important = models.BooleanField(default=False, verbose_name="Muhim")

    class Meta:
        verbose_name = "Talaba eslatmasi"
        verbose_name_plural = "Talaba eslatmalari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.title}"