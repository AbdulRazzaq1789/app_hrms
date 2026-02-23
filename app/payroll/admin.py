# payroll/admin.py
from django.contrib import admin, messages
from .models import PayrollRun, PayrollLine, BonusEntry, PrepaidEntry
from .services import calculate_payroll
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .exports import build_payroll_xlsx
from core.jalali import JALALI_MONTHS_DARI


@admin.register(BonusEntry)
class BonusEntryAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "jalali_month", "amount", "note")
    def jalali_month(self, obj):
        return JALALI_MONTHS_DARI[obj.month]
    jalali_month.short_description = "Month"
    list_filter = ("year", "month")
    search_fields = ("employee__first_name", "employee__father_name", "note")


@admin.register(PrepaidEntry)
class PrepaidEntryAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "jalali_month", "amount", "note")
    def jalali_month(self, obj):
        return JALALI_MONTHS_DARI[obj.month]
    jalali_month.short_description = 'Month'
    list_filter = ("year", "month")
    search_fields = ("employee__first_name", "employee__father_name", "note")


class PayrollLineInline(admin.TabularInline):
    model = PayrollLine
    extra = 0
    can_delete = False
    readonly_fields = (
        "employee",
        "base_salary",
        "attendance_deduction",
        "salary",
        "bonus",
        "overtime",
        "total",
        "tax",
        "prepaid",
        "amount_to_pay",
    )


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ("year", "jalali_month", "status", "created_at")
    def jalali_month(self, obj):
        return JALALI_MONTHS_DARI[obj.month]
    jalali_month.short_description = 'Month'
    list_filter = ("year", "month", "status")
    actions = ["action_calculate"]
    inlines = [PayrollLineInline]

    @admin.action(description="Calculate payroll for selected runs")
    def action_calculate(self, request, queryset):
        for run in queryset:
            calculate_payroll(run)
        self.message_user(request, "Payroll calculated successfully.", level=messages.SUCCESS)
        
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:run_id>/report/", self.admin_site.admin_view(self.report_view), name="payroll_report"),
            path("<int:run_id>/export/", self.admin_site.admin_view(self.export_view), name="payroll_export"),
        ]
        return custom + urls


    def export_view(self, request, run_id: int):
        run = get_object_or_404(PayrollRun, id=run_id)
        wb = build_payroll_xlsx(run)

        filename = f"payroll_{run.year}_{run.month:02d}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    def report_view(self, request, run_id: int):
        run = get_object_or_404(PayrollRun, id=run_id)
        lines = run.lines.select_related("employee").all()

        totals = lines.aggregate(
            base_salary=Sum("base_salary"),
            attendance_deduction=Sum("attendance_deduction"),
            salary=Sum("salary"),
            bonus=Sum("bonus"),
            overtime=Sum("overtime"),
            total=Sum("total"),
            tax=Sum("tax"),
            prepaid=Sum("prepaid"),
            amount_to_pay=Sum("amount_to_pay"),
        )

        return render(request, "admin/payroll/report.html", {
            "run": run,
            "lines": lines,
            "totals": totals,
        })