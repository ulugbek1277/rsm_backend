from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Invoice, Payment, DebtSnapshot


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['paid_amount', 'paid_at', 'method', 'note', 'receipt_number']
    readonly_fields = ['paid_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student', 'group', 'amount_display', 'remaining_amount',
        'due_date', 'status_display', 'is_overdue', 'issued_at'
    ]
    list_filter = ['status', 'due_date', 'group', 'issued_at']
    search_fields = [
        'student__first_name', 'student__last_name',
        'group__name', 'description'
    ]
    ordering = ['-issued_at']
    inlines = [PaymentInline]
    
    fieldsets = [
        ('Invoice Info', {
            'fields': [
                'student', 'group',
                ('amount', 'discount_amount'),
                'due_date', 'description'
            ]
        }),
        ('Status', {
            'fields': ['status', 'is_active']
        })
    ]
    
    readonly_fields = ['status']
    
    def amount_display(self, obj):
        if obj.discount_amount > 0:
            return format_html(
                '<span style="text-decoration: line-through;">{}</span> '
                '<span style="color: green; font-weight: bold;">{}</span>',
                f"{obj.amount:,.0f} so'm",
                f"{obj.final_amount:,.0f} so'm"
            )
        return f"{obj.amount:,.0f} so'm"
    amount_display.short_description = 'Amount'
    
    def remaining_amount(self, obj):
        remaining = obj.remaining_amount
        if remaining > 0:
            color = 'red' if obj.is_overdue else 'orange'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:,.0f} so\'m</span>',
                color, remaining
            )
        return format_html(
            '<span style="color: green;">To\'langan</span>'
        )
    remaining_amount.short_description = 'Remaining'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'partial': 'blue',
            'overdue': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">● {} kun</span>',
                obj.days_overdue
            )
        return format_html(
            '<span style="color: green;">○</span>'
        )
    is_overdue.short_description = 'Overdue'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'invoice_info', 'paid_amount', 'paid_at',
        'method_display', 'receipt_number'
    ]
    list_filter = ['method', 'paid_at', 'invoice__status']
    search_fields = [
        'invoice__student__first_name', 'invoice__student__last_name',
        'note', 'receipt_number'
    ]
    ordering = ['-paid_at']
    
    fieldsets = [
        ('Payment Info', {
            'fields': [
                'invoice', 'paid_amount', 'paid_at', 'method'
            ]
        }),
        ('Details', {
            'fields': ['note', 'receipt_number']
        }),
        ('Status', {
            'fields': ['is_active']
        })
    ]
    
    def invoice_info(self, obj):
        return f"#{obj.invoice.id} - {obj.invoice.student.get_full_name()}"
    invoice_info.short_description = 'Invoice'
    
    def method_display(self, obj):
        colors = {
            'cash': 'green',
            'card': 'blue',
            'transfer': 'orange',
            'online': 'purple',
        }
        color = colors.get(obj.method, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_method_display()
        )
    method_display.short_description = 'Method'


@admin.register(DebtSnapshot)
class DebtSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'snapshot_date', 'total_debt_display',
        'overdue_debt_display', 'overdue_days'
    ]
    list_filter = ['snapshot_date', 'overdue_days']
    search_fields = ['student__first_name', 'student__last_name']
    ordering = ['-snapshot_date', '-total_debt']
    
    fieldsets = [
        ('Snapshot Info', {
            'fields': ['snapshot_date', 'student']
        }),
        ('Debt Details', {
            'fields': [
                ('total_debt', 'overdue_debt'),
                'overdue_days'
            ]
        })
    ]
    
    def total_debt_display(self, obj):
        if obj.total_debt > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,.0f} so\'m</span>',
                obj.total_debt
            )
        return format_html(
            '<span style="color: green;">0 so\'m</span>'
        )
    total_debt_display.short_description = 'Total Debt'
    
    def overdue_debt_display(self, obj):
        if obj.overdue_debt > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,.0f} so\'m</span>',
                obj.overdue_debt
            )
        return format_html(
            '<span style="color: gray;">0 so\'m</span>'
        )
    overdue_debt_display.short_description = 'Overdue Debt'
