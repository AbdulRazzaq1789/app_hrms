from django.http import HttpResponse

from core.admin import JalaliDateAdminMixin
from jalali_date.admin import ModelAdminJalaliMixin

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .exports import build_overtime_xlsx

from employees.models import Employee
from org.models import Department
from core.jalali import jalali_month_range, jalali_day_to_gregorian
from .models import OvertimeEntry  # adjust name

@admin.register(OvertimeEntry)
class OvertimeEntryAdmin(ModelAdminJalaliMixin, JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ("employee", "date", "hours", "note")
    list_filter = ("date",)
    search_fields = ("employee__first_name", "employee__father_name", "note")

    change_list_template = "admin/overtime/overtime_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("export/", self.admin_site.admin_view(self.export_overtime_view), name="overtime_export"),
            path("bulk/", self.admin_site.admin_view(self.bulk_overtime_view), name="overtime_bulk"),
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

    def bulk_overtime_view(self, request):
        jy = int(request.GET.get("jy") or request.POST.get("jy") or 1404)
        jm = int(request.GET.get("jm") or request.POST.get("jm") or 1)
        department_id = request.GET.get("department_id") or request.POST.get("department_id") or ""

        departments = Department.objects.all().order_by("name")

        try:
            rng = jalali_month_range(jy, jm)
        except Exception:
            messages.error(request, "Invalid Jalali year/month.")
            return redirect(request.path)

        days = list(range(1, rng.days + 1))

        emp_qs = Employee.objects.filter(status=Employee.Status.WORKING).select_related("department", "position")
        if department_id:
            emp_qs = emp_qs.filter(department_id=department_id)
        employees = list(emp_qs.order_by("first_name", "father_name"))

        # SAVE
        if request.method == "POST":
            with transaction.atomic():
                for emp in employees:
                    for d in days:
                        key = f"ot_{emp.id}_{d}"
                        raw = (request.POST.get(key) or "").strip()
                        g_date = jalali_day_to_gregorian(jy, jm, d)

                        # Blank => delete
                        if raw == "":
                            OvertimeEntry.objects.filter(employee=emp, date=g_date).delete()
                            continue

                        # Parse Decimal hours
                        try:
                            hours = Decimal(raw)
                        except (InvalidOperation, ValueError):
                            continue

                        # If user typed 0 => treat as blank
                        if hours <= 0:
                            OvertimeEntry.objects.filter(employee=emp, date=g_date).delete()
                            continue

                        # save/update
                        OvertimeEntry.objects.update_or_create(
                            employee=emp,
                            date=g_date,
                            defaults={"hours": hours},
                        )

            messages.success(request, "Overtime entries saved.")
            return redirect(f"{request.path}?jy={jy}&jm={jm}&department_id={department_id}")

        # LOAD existing overtime map for the month
        entries = OvertimeEntry.objects.filter(
            date__range=(rng.g_start, rng.g_end),
            employee__in=employees,
        ).values("employee_id", "date", "hours")

        ot_map = {(e["employee_id"], e["date"]): e["hours"] for e in entries}

        rows = []
        for emp in employees:
            cells = []
            for d in days:
                g_date = jalali_day_to_gregorian(jy, jm, d)
                cells.append({"day": d, "value": ot_map.get((emp.id, g_date), "")})
            rows.append({"employee": emp, "cells": cells})

        ctx = {
            "jy": jy,
            "jm": jm,
            "department_id": department_id,
            "departments": departments,
            "loaded": (request.GET.get("jy") and request.GET.get("jm")) or request.method == "POST",
            "days": days,
            "rows": rows,
        }
        return render(request, "admin/overtime/bulk_grid.html", ctx)