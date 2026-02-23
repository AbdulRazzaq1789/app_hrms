# payroll/models.py
from django.db import models
from employees.models import Employee

class PayrollRun(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        FINAL = "FINAL", "Final"

    year = models.PositiveIntegerField()   # Jalali year
    month = models.PositiveSmallIntegerField()  # Jalali month
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Payroll {self.year}-{self.month:02d}"


class PayrollLine(models.Model):
    run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="lines")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)

    # Report fields
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    attendance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # base - attendance_deduction

    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # salary + bonus + overtime
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    prepaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # manual
    amount_to_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # total - tax - prepaid

    class Meta:
        unique_together = ("run", "employee")
        ordering = ["employee__first_name"]

    def __str__(self):
        return f"{self.run} - {self.employee}"


class BonusEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="bonuses")
    year = models.PositiveIntegerField()         # Jalali year
    month = models.PositiveSmallIntegerField()   # Jalali month
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.employee} bonus {self.year}-{self.month:02d}: {self.amount}"


class PrepaidEntry(models.Model):
    """
    Manual prepaid/advance payment.
    Important: it reduces amount_to_pay but does NOT reduce taxable amount.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="prepaids")
    year = models.PositiveIntegerField()         # Jalali year
    month = models.PositiveSmallIntegerField()   # Jalali month
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-year", "-month"]
        unique_together = ("employee", "year", "month", "note")  # allow multiple prepaids with different notes

    def __str__(self):
        return f"{self.employee} prepaid {self.year}-{self.month:02d}: {self.amount}"