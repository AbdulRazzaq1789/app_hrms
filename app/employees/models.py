from django.db import models
from django.core.validators import MinValueValidator
from org.models import Department, Position

class Employee(models.Model):
    class EmployeeType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent"
        CONTRACT = "CONTRACT", "Contract"
        DAILY = "DAILY", "Daily Worker"
        FIXED_TERM = "FIXED_TERM", "Fixed Term"

    class Status(models.TextChoices):
        WORKING = "WORKING", "Working"
        SUSPENDED = "SUSPENDED", "Suspended"
        RESIGNED = "RESIGNED", "Resigned"
        TERMINATED = "TERMINATED", "Terminated"

    first_name = models.CharField(max_length=80)
    father_name = models.CharField(max_length=80, blank=True)

    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)

    employee_type = models.CharField(max_length=20, choices=EmployeeType.choices)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    date_hired = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WORKING)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "father_name"]

    def __str__(self):
        return f"{self.first_name} {self.father_name}".strip()