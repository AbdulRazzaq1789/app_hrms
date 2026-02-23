from decimal import Decimal, ROUND_CEILING
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

def dceil2(x):
    if x is None:
        return Decimal("0.00")
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_CEILING)

def build_payroll_xlsx(run):
    wb = Workbook()
    ws = wb.active
    ws.title = f"{run.year}-{run.month:02d}"

    headers = [
        "Employee",
        "Base Salary",
        "Attendance Deduction",
        "Salary",
        "Bonus",
        "Overtime",
        "Total",
        "Tax",
        "Prepaid",
        "Amount To Pay",
    ]
    ws.append(headers)

    lines = run.lines.select_related("employee").all()

    for l in lines:
        ws.append([
            str(l.employee),
            float(dceil2(l.base_salary)),
            float(dceil2(l.attendance_deduction)),
            float(dceil2(l.salary)),
            float(dceil2(l.bonus)),
            float(dceil2(l.overtime)),
            float(dceil2(l.total)),
            float(dceil2(l.tax)),
            float(dceil2(l.prepaid)),
            float(dceil2(l.amount_to_pay)),
        ])

    # Totals row
    def sum_field(name):
        return sum((dceil2(getattr(l, name)) for l in lines), Decimal("0.00"))

    ws.append([
        "TOTALS",
        float(sum_field("base_salary")),
        float(sum_field("attendance_deduction")),
        float(sum_field("salary")),
        float(sum_field("bonus")),
        float(sum_field("overtime")),
        float(sum_field("total")),
        float(sum_field("tax")),
        float(sum_field("prepaid")),
        float(sum_field("amount_to_pay")),
    ])

    # basic column widths
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18
    ws.column_dimensions["A"].width = 28

    return wb