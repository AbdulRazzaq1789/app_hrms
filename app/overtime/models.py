from django.db import models
from django.core.validators import MinValueValidator
from employees.models import Employee

class OvertimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="overtime_entries")
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} {self.date} {self.hours}h"