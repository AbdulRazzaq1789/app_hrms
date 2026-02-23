from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class MonthConfig(models.Model):
    year = models.PositiveIntegerField()  # Jalali year
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])  # Jalali month

    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    daily_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8)

    # ✅ Monthly paid leave cap (your current rule: 5)
    monthly_paid_leave_cap = models.PositiveSmallIntegerField(default=5)

    class Meta:
        unique_together = ("year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.year}-{self.month:02d}"