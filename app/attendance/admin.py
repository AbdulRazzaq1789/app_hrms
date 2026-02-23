from __future__ import annotations

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.db import transaction

from .models import AttendanceDay
from employees.models import Employee
from org.models import Department
from core.jalali import jalali_month_range, jalali_day_to_gregorian, format_gregorian_to_jalali_with_day
from django.http import HttpResponse
from .exports import build_attendance_xlsx
from employees.models import Employee
from jalali_date.admin import ModelAdminJalaliMixin
from core.admin import JalaliDateAdminMixin

@admin.register(AttendanceDay)
class AttendanceDayAdmin(ModelAdminJalaliMixin, JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ("jalali_date", "employee", "status", "note")
    def jalali_date(self, obj):
        return format_gregorian_to_jalali_with_day(obj.date)
    jalali_date.short_description = "Date"

    list_filter = ("status", "date")
    search_fields = ("employee__first_name", "employee__father_name", "note")

    change_list_template = "admin/attendance/attendance_changelist.html"
    
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("bulk/", self.admin_site.admin_view(self.bulk_attendance_view), name="attendance_bulk"),
            path("export/", self.admin_site.admin_view(self.export_attendance_view), name="attendance_export"),
        ]
        return custom + urls


    def export_attendance_view(self, request):
        # expects ?jy=1404&jm=12&department_id=...
        jy = int(request.GET.get("jy") or 1404)
        jm = int(request.GET.get("jm") or 1)
        department_id = request.GET.get("department_id") or ""

        emp_qs = Employee.objects.filter(status=Employee.Status.WORKING).select_related("department", "position")
        if department_id:
            emp_qs = emp_qs.filter(department_id=department_id)
        employees = list(emp_qs.order_by("first_name", "father_name"))

        wb = build_attendance_xlsx(jy, jm, employees)

        filename = f"attendance_{jy}_{jm:02d}.xlsx"
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    def bulk_attendance_view(self, request):
        # GET params
        jy = int(request.GET.get("jy") or request.POST.get("jy") or 1404)
        jm = int(request.GET.get("jm") or request.POST.get("jm") or 1)
        department_id = request.GET.get("department_id") or request.POST.get("department_id") or ""

        departments = Department.objects.all().order_by("name")

        loaded = request.method == "GET" and request.GET.get("jy") and request.GET.get("jm")
        rows = []
        days = []


        

        # Load month range (Jalali -> Gregorian range)
        try:
            rng = jalali_month_range(jy, jm)
        except Exception:
            messages.error(request, "Invalid Jalali year/month.")
            return redirect(request.path)

        days = list(range(1, rng.days + 1))

        # compute friday days
        friday_days = set()
        for d in days:
            g = jalali_day_to_gregorian(jy, jm, d)
            if g.weekday() == 4:
                friday_days.add(d)

        # Employee query
        emp_qs = Employee.objects.filter(status=Employee.Status.WORKING).select_related("department", "position")
        if department_id:
            emp_qs = emp_qs.filter(department_id=department_id)

        employees = list(emp_qs.order_by("first_name", "father_name"))

        # If POST: save exceptions
        if request.method == "POST":
            with transaction.atomic():
                for emp in employees:
                    for d in days:
                        key = f"st_{emp.id}_{d}"
                        val = (request.POST.get(key) or "").strip()

                        g_date = jalali_day_to_gregorian(jy, jm, d)

                        # ✅ ENFORCE: Friday cannot be changed / stored
                        if d in friday_days:
                            # ensure nothing is stored for Fridays
                            AttendanceDay.objects.filter(employee=emp, date=g_date).delete()
                            continue

                        obj = AttendanceDay.objects.filter(employee=emp, date=g_date).first()

                        # Blank means OK/present -> delete exception if exists
                        if val == "":
                            if obj:
                                obj.delete()
                            continue

                        if val not in (AttendanceDay.Status.ABSENT, AttendanceDay.Status.SHIFT_OFF, AttendanceDay.Status.HOLIDAY, AttendanceDay.Status.LEAVE):
                            continue

                        if obj:
                            obj.status = val
                            obj.save(update_fields=["status"])
                        else:
                            AttendanceDay.objects.create(employee=emp, date=g_date, status=val)

            messages.success(request, "Attendance exceptions saved.")
            # reload as GET to prevent resubmission
            return redirect(f"{request.path}?jy={jy}&jm={jm}&department_id={department_id}")

        # Build existing exception map for display
        if loaded or request.method == "POST" or (request.GET.get("jy") and request.GET.get("jm")):
            # Preload exceptions in the gregorian range
            exceptions = AttendanceDay.objects.filter(
                date__range=(rng.g_start, rng.g_end),
                employee__in=employees,
            ).values("employee_id", "date", "status")

            exc_map = {(e["employee_id"], e["date"]): e["status"] for e in exceptions}

            for emp in employees:
                cells = []
                for d in days:
                    g_date = jalali_day_to_gregorian(jy, jm, d)
                    cells.append({"day": d, "value": exc_map.get((emp.id, g_date), "")})
                rows.append({"employee": emp, "cells": cells})

        ctx = {
            "jy": jy,
            "jm": jm,
            "department_id": department_id,
            "departments": departments,
            "loaded": (request.GET.get("jy") and request.GET.get("jm")) or request.method == "POST",
            "days": days,
            "rows": rows,
            "friday_days": friday_days,
        }
        return render(request, "admin/attendance/bulk_grid.html", ctx)