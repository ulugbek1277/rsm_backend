import re
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_phone_number(phone):
    """
    Validate Uzbekistan phone number format
    """
    pattern = r'^\+998[0-9]{9}$'
    if not re.match(pattern, phone):
        raise ValidationError('Telefon raqam formati: +998XXXXXXXXX')
    return phone


def mask_phone_number(phone):
    """
    Mask phone number for privacy: +998901234567 -> +998901***567
    """
    if len(phone) >= 10:
        return phone[:7] + '***' + phone[-3:]
    return phone


def validate_file_upload(file: UploadedFile):
    """
    Validate uploaded file size and format
    """
    # Check file size (20MB max)
    if file.size > 20 * 1024 * 1024:
        raise ValidationError('Fayl hajmi 20MB dan oshmasligi kerak')
    
    # Check file extension
    allowed_extensions = ['.pdf', '.docx', '.zip', '.png', '.jpg', '.jpeg']
    file_extension = file.name.lower().split('.')[-1]
    if f'.{file_extension}' not in allowed_extensions:
        raise ValidationError(
            f'Ruxsat etilgan fayl formatlari: {", ".join(allowed_extensions)}'
        )
    
    return file


def generate_slug(text):
    """
    Generate URL-friendly slug from text
    """
    # Replace spaces and special characters
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


class PhoneNumberMixin:
    """
    Mixin to add phone number masking functionality
    """
    def get_masked_phone(self):
        if hasattr(self, 'phone') and self.phone:
            return mask_phone_number(self.phone)
        return None