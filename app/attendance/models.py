from django.db import models
from employees.models import Employee

class AttendanceDay(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        SHIFT_OFF = "SHIFT_OFF", "Shift Off"     # even/odd schedule off day
        HOLIDAY = "HOLIDAY", "Holiday"
        LEAVE = "LEAVE", "Leave"
        
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_days")
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date", "employee__first_name"]

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"