from django.contrib import admin
from .models import LeaveType, LeaveYearBalance, LeaveEntry
from django import forms
from jalali_date.admin import ModelAdminJalaliMixin
from core.admin import JalaliDateAdminMixin
from core.jalali import format_gregorian_to_jalali


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "yearly_limit_days", "is_paid")
    search_fields = ("name",)

@admin.register(LeaveYearBalance)
class LeaveYearBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "leave_type", "remaining_days")
    list_filter = ("year", "leave_type")
    search_fields = ("employee__first_name", "employee__father_name")

class LeaveEntryForm(forms.ModelForm):
    class Meta:
        model = LeaveEntry
        fields = ("employee", "leave_type", "date_from", "days_count", "note")

@admin.register(LeaveEntry)
class LeaveEntryAdmin(ModelAdminJalaliMixin, JalaliDateAdminMixin, admin.ModelAdmin):
    form = LeaveEntryForm
    list_display = ("employee", "leave_type", "date_from_jalali", "date_to_jalali", "days_count", "excess_days")
    def date_from_jalali(self, obj):
        return format_gregorian_to_jalali(obj.date_from)
    date_from_jalali.short_description = "Date From"
    def date_to_jalali(self, obj):
        return format_gregorian_to_jalali(obj.date_from)
    date_to_jalali.short_description = "To"
    list_filter = ("leave_type", "date_from")
    search_fields = ("employee__first_name", "employee__father_name", "note")

    def save_model(self, request, obj, form, change):
        # Compute end date already happens in obj.save()
        super().save_model(request, obj, form, change)

        # update balances + mark excess
        obj.apply_balance()
        obj.save(update_fields=["excess_days", "date_to"])

        # fill attendance exceptions as LEAVE
        obj.sync_attendance()