from django.contrib import admin
from .models import Employee
from jalali_date.admin import ModelAdminJalaliMixin
from core.admin import JalaliDateAdminMixin
from core.jalali import format_gregorian_to_jalali


@admin.register(Employee)
class EmployeeAdmin(ModelAdminJalaliMixin,JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ("first_name", "father_name", "department", "position", "employee_type", "base_salary", "status", "date_hired_jalali")
    def date_hired_jalali(self, obj):
        return format_gregorian_to_jalali(obj.date_hired)
    date_hired_jalali.short_description = 'Date Hired'
    list_filter = ("department", "employee_type", "status")
    search_fields = ("first_name", "father_name", "phone")