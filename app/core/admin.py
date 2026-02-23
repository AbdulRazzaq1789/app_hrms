from django.contrib import admin
from .models import MonthConfig
from core.jalali import JALALI_MONTHS_DARI
from django.contrib import admin

class JalaliDateAdminMixin(admin.ModelAdmin):
    class Media:
        js = (
            "admin\js\disable_autocomplete.js",
        )
        

@admin.register(MonthConfig)
class MonthConfigAdmin(admin.ModelAdmin):
    list_display = ("year", "jalali_month", "daily_work_hours", "overtime_rate", "monthly_paid_leave_cap")
    def jalali_month(self, obj):
        return JALALI_MONTHS_DARI[obj.month]
    jalali_month.short_description = 'Month'
    list_filter = ("year", "month")