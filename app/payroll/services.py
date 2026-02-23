# payroll/services.py
from __future__ import annotations

from decimal import Decimal
from django.db import transaction, models
import datetime as dt
import jdatetime

from core.models import MonthConfig
from core.jalali import jalali_month_range
from employees.models import Employee
from attendance.models import AttendanceDay
from leaves.models import LeaveEntry, LeaveType, LeaveYearBalance
from overtime.models import OvertimeEntry
from payroll.models import PayrollRun, PayrollLine, BonusEntry, PrepaidEntry


def calculate_progressive_tax(amount: Decimal) -> Decimal:
    amount = Decimal(amount)
    if amount <= 0:
        return Decimal("0.00")

    tax = Decimal("0.00")
    slabs = [
        (Decimal("5000"),   Decimal("0.00")),
        (Decimal("12500"),  Decimal("0.02")),
        (Decimal("100000"), Decimal("0.10")),
        (None,              Decimal("0.20")),
    ]

    prev = Decimal("0")
    for limit, rate in slabs:
        if limit is None:
            part = amount - prev
        else:
            part = min(amount, limit) - prev

        if part > 0:
            tax += part * rate

        if limit is not None and amount <= limit:
            break
        if limit is not None:
            prev = limit

    return tax.quantize(Decimal("0.01"))


@transaction.atomic
def calculate_payroll(run: PayrollRun):
    jy, jm = run.year, run.month
    rng = jalali_month_range(jy, jm)  # gregorian start/end

    cfg, _ = MonthConfig.objects.get_or_create(
        year=jy,
        month=jm,
        defaults={
            "daily_work_hours": 8,
            "overtime_rate": 1,
            "monthly_paid_leave_cap": 5,
        },
    )

    # Fridays count inside this Jalali month range
    fridays = 0
    cur = rng.g_start
    while cur <= rng.g_end:
        if cur.weekday() == 4:
            fridays += 1
        cur += dt.timedelta(days=1)

    working_days = 26

    daily_work_hours = Decimal(cfg.daily_work_hours) if cfg.daily_work_hours else Decimal("8")
    overtime_rate = Decimal(cfg.overtime_rate)

    auto_leave_type = LeaveType.objects.filter(auto_cover_absence=True, is_paid=True).first()

    run.lines.all().delete()

    employees = Employee.objects.filter(status=Employee.Status.WORKING)

    for emp in employees:
        base_salary = Decimal(emp.base_salary)
        daily_rate = base_salary / Decimal(working_days)

        # ABSENT days (exceptions-only)
        absent_days = Decimal(
            AttendanceDay.objects.filter(
                employee=emp,
                date__range=(rng.g_start, rng.g_end),
                status=AttendanceDay.Status.ABSENT,
            ).count()
        )

        # Auto-cover ABSENT with paid leave (yearly remaining + monthly cap)
        auto_paid_leave_days = Decimal("0")
        unpaid_absent_days = absent_days

        if auto_leave_type and absent_days > 0:
            already_taken = LeaveEntry.objects.filter(
                employee=emp,
                leave_type=auto_leave_type,
                date_from__lte=rng.g_end,
                date_to__gte=rng.g_start,
            ).aggregate(total=models.Sum("days_count"))["total"] or Decimal("0")

            monthly_cap = Decimal(cfg.monthly_paid_leave_cap)
            monthly_available = max(Decimal("0"), monthly_cap - Decimal(already_taken))

            bal, _ = LeaveYearBalance.objects.get_or_create(
                employee=emp,
                year=jy,  # Jalali year
                leave_type=auto_leave_type,
                defaults={"remaining_days": Decimal(auto_leave_type.yearly_limit_days)},
            )
            yearly_available = Decimal(bal.remaining_days)

            auto_paid_leave_days = min(absent_days, monthly_available, yearly_available)

            if auto_paid_leave_days > 0:
                bal.remaining_days = yearly_available - auto_paid_leave_days
                bal.save(update_fields=["remaining_days"])
                unpaid_absent_days = absent_days - auto_paid_leave_days

        # Attendance deduction is only unpaid absences
        attendance_deduction = (daily_rate * unpaid_absent_days).quantize(Decimal("0.01"))

        salary = (base_salary - attendance_deduction).quantize(Decimal("0.01"))

        # Overtime amount
        overtime_hours = OvertimeEntry.objects.filter(
            employee=emp,
            date__range=(rng.g_start, rng.g_end),
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0")

        monthly_work_hours = Decimal(working_days) * daily_work_hours
        hourly_salary = (base_salary / monthly_work_hours) if monthly_work_hours else Decimal("0")
        overtime_amount = (Decimal(overtime_hours) * overtime_rate * hourly_salary).quantize(Decimal("0.01"))

        # Bonus
        bonus_amount = BonusEntry.objects.filter(
            employee=emp, year=jy, month=jm
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        bonus_amount = Decimal(bonus_amount).quantize(Decimal("0.01"))

        total = (salary + bonus_amount + overtime_amount).quantize(Decimal("0.01"))

        # Tax is calculated from TOTAL (prepaid does not reduce tax base)
        tax_amount = calculate_progressive_tax(total)

        # Prepaid sum (manual)
        prepaid_amount = PrepaidEntry.objects.filter(
            employee=emp, year=jy, month=jm
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        prepaid_amount = Decimal(prepaid_amount).quantize(Decimal("0.01"))

        amount_to_pay = (total - tax_amount - prepaid_amount).quantize(Decimal("0.01"))

        PayrollLine.objects.create(
            run=run,
            employee=emp,
            base_salary=base_salary,
            attendance_deduction=attendance_deduction,
            salary=salary,
            bonus=bonus_amount,
            overtime=overtime_amount,
            total=total,
            tax=tax_amount,
            prepaid=prepaid_amount,
            amount_to_pay=amount_to_pay,
        )