import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import SmsLog, Broadcast, SmsTemplate


class SMSProvider:
    """
    SMS provider interface
    """
    def send_sms(self, phone, message):
        raise NotImplementedError


class EskizSMSProvider(SMSProvider):
    """
    Eskiz.uz SMS provider
    """
    def __init__(self):
        self.api_url = settings.SMS_API_URL
        self.api_key = settings.SMS_API_KEY
    
    def send_sms(self, phone, message):
        """
        Send SMS via Eskiz.uz API
        """
        if not self.api_key:
            raise Exception("SMS API key not configured")
        
        payload = {
            'mobile_phone': phone,
            'message': message,
            'from': '4546',  # Default sender
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('status') == 'success':
                return {
                    'success': True,
                    'provider_id': result.get('id'),
                    'message': 'SMS sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error')
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }


class MockSMSProvider(SMSProvider):
    """
    Mock SMS provider for testing
    """
    def send_sms(self, phone, message):
        """
        Mock SMS sending - always returns success
        """
        import time
        import random
        
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simulate occasional failures (5% chance)
        if random.random() < 0.05:
            return {
                'success': False,
                'error': 'Mock network error'
            }
        
        return {
            'success': True,
            'provider_id': f'mock_{int(time.time())}',
            'message': 'Mock SMS sent successfully'
        }


def get_sms_provider():
    """
    Get SMS provider based on settings
    """
    provider_type = getattr(settings, 'SMS_PROVIDER', 'mock')
    
    if provider_type == 'eskiz':
        return EskizSMSProvider()
    else:
        return MockSMSProvider()


@shared_task(bind=True, max_retries=3)
def send_sms(self, phone, message, template_id=None):
    """
    Send single SMS
    """
    # Create SMS log entry
    sms_log = SmsLog.objects.create(
        recipient_phone=phone,
        message=message,
        template_id=template_id,
        status='pending'
    )
    
    try:
        provider = get_sms_provider()
        result = provider.send_sms(phone, message)
        
        if result['success']:
            sms_log.mark_as_sent(result.get('provider_id'))
            return f"SMS sent to {phone}"
        else:
            sms_log.mark_as_failed(result['error'])
            # Retry on failure
            raise Exception(result['error'])
    
    except Exception as exc:
        sms_log.mark_as_failed(str(exc))
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return f"Failed to send SMS to {phone}: {str(exc)}"


@shared_task
def send_broadcast_sms(broadcast_id):
    """
    Send SMS broadcast to multiple recipients
    """
    try:
        broadcast = Broadcast.objects.get(id=broadcast_id)
    except Broadcast.DoesNotExist:
        return f"Broadcast {broadcast_id} not found"
    
    recipients = broadcast.get_recipients()
    
    for phone in recipients:
        # Queue individual SMS
        send_sms.delay(phone, broadcast.content)
    
    # Update broadcast status
    broadcast.mark_as_completed()
    
    return f"Queued {len(recipients)} SMS messages for broadcast {broadcast_id}"


@shared_task
def send_absence_notification(attendance_record_id):
    """
    Send absence notification to parent
    """
    from apps.attendance.models import AttendanceRecord
    
    try:
        record = AttendanceRecord.objects.get(id=attendance_record_id)
    except AttendanceRecord.DoesNotExist:
        return f"Attendance record {attendance_record_id} not found"
    
    # Get student and parent info
    student = record.student
    if not hasattr(student, 'student_profile'):
        return f"Student {student.id} has no profile"
    
    parent_phone = student.student_profile.parent_phone
    parent_name = student.student_profile.parent_name
    
    if not parent_phone:
        return f"No parent phone for student {student.id}"
    
    # Get SMS template
    try:
        template = SmsTemplate.objects.get(code='ABSENCE_NOTIFICATION', is_active=True)
    except SmsTemplate.DoesNotExist:
        # Create default template if not exists
        template = SmsTemplate.objects.create(
            code='ABSENCE_NOTIFICATION',
            name='Yo\'qlik haqida xabar',
            text='Hurmatli {parent_name}, {student_name} bugun {date} sanasida {group_name} darsiga kelmadi. Ma\'lumot uchun: {center_phone}',
            description='O\'quvchi darsga kelmagan holda ota-onaga yuboriladi'
        )
    
    # Render message
    context = {
        'parent_name': parent_name,
        'student_name': student.get_full_name(),
        'date': record.session.date.strftime('%d.%m.%Y'),
        'group_name': record.session.group.name,
        'center_phone': getattr(settings, 'CENTER_PHONE', '+998901234567')
    }
    
    message = template.render(context)
    
    # Send SMS
    send_sms.delay(parent_phone, message, template.id)
    
    return f"Absence notification queued for {student.get_full_name()}"


@shared_task
def send_schedule_change_notification(override_id):
    """
    Send schedule change notification
    """
    from apps.schedules.models import CalendarOverride
    
    try:
        override = CalendarOverride.objects.get(id=override_id)
    except CalendarOverride.DoesNotExist:
        return f"Calendar override {override_id} not found"
    
    # Get SMS template
    try:
        template = SmsTemplate.objects.get(code='SCHEDULE_CHANGE', is_active=True)
    except SmsTemplate.DoesNotExist:
        template = SmsTemplate.objects.create(
            code='SCHEDULE_CHANGE',
            name='Jadval o\'zgarishi',
            text='Hurmatli ota-onalar, {date} sanasida {group_name} guruhi darsi {status}. {note} Ma\'lumot: {center_phone}',
            description='Dars jadvali o\'zgarganda yuboriladi'
        )
    
    # Determine affected groups
    if override.group:
        groups = [override.group]
    else:
        # All groups (center closure)
        from apps.groups.models import Group
        groups = Group.objects.filter(status='active', is_active=True)
    
    # Get parent phones
    parent_phones = set()
    for group in groups:
        phones = group.students.filter(
            is_active=True,
            student__student_profile__isnull=False
        ).values_list('student__student_profile__parent_phone', flat=True)
        parent_phones.update(phones)
    
    # Render message
    status_text = "bekor qilindi" if override.is_canceled else "o'zgartirildi"
    context = {
        'date': override.date.strftime('%d.%m.%Y'),
        'group_name': override.group.name if override.group else "barcha guruhlar",
        'status': status_text,
        'note': override.note or "",
        'center_phone': getattr(settings, 'CENTER_PHONE', '+998901234567')
    }
    
    message = template.render(context)
    
    # Send SMS to all parents
    for phone in parent_phones:
        if phone:
            send_sms.delay(phone, message, template.id)
    
    return f"Schedule change notification queued for {len(parent_phones)} parents"


@shared_task
def send_payment_reminders():
    """
    Send payment reminders for due invoices
    """
    from apps.payments.models import Invoice
    from datetime import timedelta
    
    # Get invoices due in 3 days
    reminder_date = timezone.now().date() + timedelta(days=3)
    
    due_invoices = Invoice.objects.filter(
        due_date=reminder_date,
        status__in=['pending', 'partial'],
        is_active=True
    )
    
    # Get SMS template
    try:
        template = SmsTemplate.objects.get(code='PAYMENT_REMINDER', is_active=True)
    except SmsTemplate.DoesNotExist:
        template = SmsTemplate.objects.create(
            code='PAYMENT_REMINDER',
            name='To\'lov eslatmasi',
            text='Hurmatli {parent_name}, {student_name} uchun {amount} so\'m to\'lov {due_date} sanasigacha amalga oshirilishi kerak. Ma\'lumot: {center_phone}',
            description='To\'lov muddati yaqinlashganda yuboriladi'
        )
    
    sent_count = 0
    
    for invoice in due_invoices:
        student = invoice.student
        if not hasattr(student, 'student_profile'):
            continue
        
        parent_phone = student.student_profile.parent_phone
        parent_name = student.student_profile.parent_name
        
        if not parent_phone:
            continue
        
        # Render message
        context = {
            'parent_name': parent_name,
            'student_name': student.get_full_name(),
            'amount': f"{invoice.remaining_amount:,.0f}",
            'due_date': invoice.due_date.strftime('%d.%m.%Y'),
            'center_phone': getattr(settings, 'CENTER_PHONE', '+998901234567')
        }
        
        message = template.render(context)
        
        # Send SMS
        send_sms.delay(parent_phone, message, template.id)
        sent_count += 1
    
    return f"Payment reminders queued for {sent_count} invoices"


@shared_task
def send_debt_notifications():
    """
    Send debt notifications for overdue invoices
    """
    from apps.payments.models import Invoice
    
    # Get overdue invoices
    today = timezone.now().date()
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['pending', 'partial', 'overdue'],
        is_active=True
    )
    
    # Get SMS template
    try:
        template = SmsTemplate.objects.get(code='DEBT_NOTIFICATION', is_active=True)
    except SmsTemplate.DoesNotExist:
        template = SmsTemplate.objects.create(
            code='DEBT_NOTIFICATION',
            name='Qarz haqida xabar',
            text='Hurmatli {parent_name}, {student_name} uchun {debt_amount} so\'m qarz mavjud. Iltimos, tezroq to\'lang. Ma\'lumot: {center_phone}',
            description='Qarzdorlik haqida xabar'
        )
    
    # Group by student to avoid multiple messages
    student_debts = {}
    for invoice in overdue_invoices:
        student_id = invoice.student.id
        if student_id not in student_debts:
            student_debts[student_id] = {
                'student': invoice.student,
                'total_debt': 0
            }
        student_debts[student_id]['total_debt'] += invoice.remaining_amount
    
    sent_count = 0
    
    for student_data in student_debts.values():
        student = student_data['student']
        total_debt = student_data['total_debt']
        
        if not hasattr(student, 'student_profile'):
            continue
        
        parent_phone = student.student_profile.parent_phone
        parent_name = student.student_profile.parent_name
        
        if not parent_phone:
            continue
        
        # Render message
        context = {
            'parent_name': parent_name,
            'student_name': student.get_full_name(),
            'debt_amount': f"{total_debt:,.0f}",
            'center_phone': getattr(settings, 'CENTER_PHONE', '+998901234567')
        }
        
        message = template.render(context)
        
        # Send SMS
        send_sms.delay(parent_phone, message, template.id)
        sent_count += 1
    
    return f"Debt notifications queued for {sent_count} students"
