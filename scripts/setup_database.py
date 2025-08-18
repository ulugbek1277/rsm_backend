"""
Ma'lumotlar bazasini sozlash skripti
Bu skript ma'lumotlar bazasini yaratish va migratsiyalarni ishga tushirish uchun
"""

import os
import sys
import django
import subprocess

# Django sozlamalarini yuklash
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def run_command(command):
    """Komandani ishga tushirish"""
    print(f"🔄 Ishga tushirilmoqda: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Muvaffaqiyatli: {command}")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Xatolik: {command}")
        if result.stderr:
            print(result.stderr)
        return False
    return True

def setup_database():
    """Ma'lumotlar bazasini sozlash"""
    print("🚀 Ma'lumotlar bazasi sozlanmoqda...\n")
    
    # 1. Migratsiya fayllarini yaratish
    commands = [
        "python manage.py makemigrations accounts",
        "python manage.py makemigrations courses", 
        "python manage.py makemigrations rooms",
        "python manage.py makemigrations groups",
        "python manage.py makemigrations schedules",
        "python manage.py makemigrations attendance",
        "python manage.py makemigrations payments",
        "python manage.py makemigrations messaging",
        "python manage.py makemigrations tasks",
        "python manage.py makemigrations settings",
        "python manage.py makemigrations",
    ]
    
    for command in commands:
        if not run_command(command):
            print("❌ Migratsiya yaratishda xatolik yuz berdi")
            return False
    
    # 2. Migratsiyalarni ishga tushirish
    if not run_command("python manage.py migrate"):
        print("❌ Migratsiya ishga tushirishda xatolik yuz berdi")
        return False
    
    # 3. Static fayllarni yig'ish
    if not run_command("python manage.py collectstatic --noinput"):
        print("❌ Static fayllarni yig'ishda xatolik yuz berdi")
        return False
    
    print("\n🎉 Ma'lumotlar bazasi muvaffaqiyatli sozlandi!")
    print("\nKeyingi qadamlar:")
    print("1. python scripts/create_sample_data.py - Sample ma'lumotlar yaratish")
    print("2. python manage.py runserver - Serverni ishga tushirish")
    print("3. celery -A config worker -l info - Celery ishga tushirish")
    
    return True

if __name__ == '__main__':
    setup_database()
