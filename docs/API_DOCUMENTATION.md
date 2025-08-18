# EduMaster CRM API Hujjatlari

## Autentifikatsiya

Barcha API so'rovlari JWT token bilan himoyalangan. Token olish uchun login endpoint dan foydalaning.

### Login
\`\`\`http
POST /api/accounts/login/
Content-Type: application/json

{
    "phone_number": "+998901234567",
    "password": "your_password"
}
\`\`\`

**Javob:**
\`\`\`json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "phone_number": "+998901234567",
        "first_name": "John",
        "last_name": "Doe",
        "role": "teacher"
    }
}
\`\`\`

### Token ishlatish
Har bir so'rovda Authorization header qo'shing:
\`\`\`http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
\`\`\`

## Foydalanuvchilar API

### Foydalanuvchilar ro'yxati
\`\`\`http
GET /api/accounts/users/
\`\`\`

### Yangi foydalanuvchi yaratish
\`\`\`http
POST /api/accounts/users/
Content-Type: application/json

{
    "phone_number": "+998901234567",
    "first_name": "John",
    "last_name": "Doe",
    "role": "teacher",
    "password": "secure_password"
}
\`\`\`

### Profil ma'lumotlari
\`\`\`http
GET /api/accounts/profile/
\`\`\`

## Kurslar API

### Kurslar ro'yxati
\`\`\`http
GET /api/courses/
\`\`\`

**Query parametrlari:**
- `search` - qidiruv
- `is_active` - faol kurslar
- `ordering` - tartiblash

### Yangi kurs yaratish
\`\`\`http
POST /api/courses/
Content-Type: application/json

{
    "title": "Python dasturlash",
    "description": "Python dasturlash kursi",
    "price": "500000.00",
    "duration_months": 6,
    "is_active": true
}
\`\`\`

## Guruhlar API

### Guruhlar ro'yxati
\`\`\`http
GET /api/groups/
\`\`\`

### Yangi guruh yaratish
\`\`\`http
POST /api/groups/
Content-Type: application/json

{
    "name": "Python-01",
    "course": 1,
    "teacher": 2,
    "start_date": "2024-01-15",
    "max_students": 15
}
\`\`\`

### Guruhga o'quvchi qo'shish
\`\`\`http
POST /api/groups/{id}/add_student/
Content-Type: application/json

{
    "student_id": 5
}
\`\`\`

## Davomat API

### Davomat sessiyalari
\`\`\`http
GET /api/attendance/sessions/
\`\`\`

### Yangi davomat sessiyasi
\`\`\`http
POST /api/attendance/sessions/
Content-Type: application/json

{
    "group": 1,
    "date": "2024-01-15",
    "topic": "Python asoslari",
    "notes": "Birinchi dars"
}
\`\`\`

### Davomat belgilash
\`\`\`http
POST /api/attendance/sessions/{id}/mark_attendance/
Content-Type: application/json

{
    "attendance_data": [
        {
            "student_id": 1,
            "status": "present"
        },
        {
            "student_id": 2,
            "status": "absent",
            "reason": "Kasal"
        }
    ]
}
\`\`\`

## To'lovlar API

### Hisob-kitoblar ro'yxati
\`\`\`http
GET /api/payments/invoices/
\`\`\`

### Yangi hisob-kitob
\`\`\`http
POST /api/payments/invoices/
Content-Type: application/json

{
    "student": 1,
    "amount": "300000.00",
    "due_date": "2024-02-15",
    "description": "Yanvar oyi uchun to'lov"
}
\`\`\`

### To'lov qayd etish
\`\`\`http
POST /api/payments/payments/
Content-Type: application/json

{
    "invoice": 1,
    "amount": "300000.00",
    "payment_method": "cash",
    "notes": "Naqd to'lov"
}
\`\`\`

## SMS API

### SMS yuborish
\`\`\`http
POST /api/messaging/send-sms/
Content-Type: application/json

{
    "phone_numbers": ["+998901234567", "+998901234568"],
    "message": "Test xabar",
    "template_id": 1
}
\`\`\`

### SMS tarixi
\`\`\`http
GET /api/messaging/sms-logs/
\`\`\`

## Xatoliklar

API quyidagi HTTP status kodlarini qaytaradi:

- `200` - Muvaffaqiyatli
- `201` - Yaratildi
- `400` - Noto'g'ri so'rov
- `401` - Autentifikatsiya talab qilinadi
- `403` - Ruxsat yo'q
- `404` - Topilmadi
- `500` - Server xatosi

**Xatolik formati:**
\`\`\`json
{
    "error": "Xatolik tavsifi",
    "details": {
        "field_name": ["Maydon xatosi"]
    }
}
\`\`\`

## Pagination

Ro'yxat API lari pagination ishlatadi:

\`\`\`json
{
    "count": 100,
    "next": "http://api.example.com/accounts/?page=3",
    "previous": "http://api.example.com/accounts/?page=1",
    "results": [...]
}
\`\`\`

Query parametrlari:
- `page` - sahifa raqami
- `page_size` - sahifadagi elementlar soni (max 100)
