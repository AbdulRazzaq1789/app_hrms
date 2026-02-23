from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

from .models import OvertimeEntry
from .exports import build_overtime_xlsx
from employees.models import Employee
from core.jalali import format_gregorian_to_jalali_with_day, format_gregorian_to_jalali
from core.admin import JalaliDateAdminMixin
from jalali_date.admin import ModelAdminJalaliMixin


@admin.register(OvertimeEntry)
class OvertimeEntryAdmin(ModelAdminJalaliMixin, JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ("jalali_date", "employee", "hours", "note")
    def jalali_date(self, obj):
        return format_gregorian_to_jalali_with_day(obj.date)
    jalali_date.short_description = "Date"
    list_filter = ("date",)
    search_fields = ("employee__first_name", "employee__father_name", "note")

    change_list_template = "admin/overtime/overtime_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("export/", self.admin_site.admin_view(self.export_overtime_view), name="overtime_export"),
        ]
        return custom + urls

    def export_overtime_view(self, request):
        jy = int(request.GET.get("jy") or 1404)
        jm = int(request.GET.get("jm") or 1)
        department_id = request.GET.get("department_id") or ""

        emp_qs = Employee.objects.filter(status=Employee.Status.WORKING).select_related("department", "position")
        if department_id:
            emp_qs = emp_qs.filter(department_id=department_id)
        employees = list(emp_qs.order_by("first_name", "father_name"))

        wb = build_overtime_xlsx(jy, jm, employees)

        filename = f"overtime_{jy}_{jm:02d}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response