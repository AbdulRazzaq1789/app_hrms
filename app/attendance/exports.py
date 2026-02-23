from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import datetime as dt

from core.jalali import jalali_month_range, jalali_day_to_gregorian
from attendance.models import AttendanceDay
from core.jalali import get_weekday_names_from_jalali

STATUS_CODE = {
    "ABSENT": "غیر حاضر",
    "SHIFT_OFF": "نوبتی",
    "HOLIDAY": "رخصتی",
    "LEAVE": "رخصت",
}

def build_attendance_xlsx(jy: int, jm: int, employees):
    rng = jalali_month_range(jy, jm)
    days = list(range(1, rng.days + 1))

    # Determine which Jalali days are Fridays (by checking Gregorian weekday)
    friday_days = set()
    for d in days:
        g = jalali_day_to_gregorian(jy, jm, d)
        if g.weekday() == 4:  # Friday
            friday_days.add(d)

    wb = Workbook()
    ws = wb.active
    ws.title = f"{jy}-{jm:02d}"

    # Header: mark Friday columns
    headers = ["Employee"] + [f"{jy}-{jm}-{d} {get_weekday_names_from_jalali(jy,jm,d)[1]}" for d in days for d in days]
    ws.append(headers)

    # Preload exceptions
    exceptions = AttendanceDay.objects.filter(
        employee__in=employees,
        date__range=(rng.g_start, rng.g_end),
    ).values("employee_id", "date", "status")

    exc_map = {(e["employee_id"], e["date"]): e["status"] for e in exceptions}

    for emp in employees:
        row = [str(emp)]
        for d in days:
            g_date = jalali_day_to_gregorian(jy, jm, d)

            # Default fill:
            if d in friday_days:
                cell = "جمعه"   # Friday
            else:
                cell = "حاضر"   # Present

            # Override if exception exists
            st = exc_map.get((emp.id, g_date))
            if st:
                cell = STATUS_CODE.get(st, st)

            row.append(cell)

        ws.append(row)

    # widths
    ws.column_dimensions["A"].width = 28
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 7
    return wb