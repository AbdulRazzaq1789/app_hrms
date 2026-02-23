from django.db import models, transaction
from django.core.validators import MinValueValidator
from employees.models import Employee
import jdatetime

class LeaveType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    yearly_limit_days = models.PositiveSmallIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    auto_cover_absence = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveYearBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_balances")
    year = models.PositiveIntegerField()
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    remaining_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        unique_together = ("employee", "year", "leave_type")
        ordering = ["-year", "employee__first_name"]

    def __str__(self):
        return f"{self.employee} {self.year} {self.leave_type}: {self.remaining_days}"


from django.db import models, transaction
from django.core.validators import MinValueValidator
import datetime as dt
import jdatetime

from employees.models import Employee
from attendance.models import AttendanceDay  # ✅

class LeaveEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_entries")
    leave_type = models.ForeignKey("LeaveType", on_delete=models.PROTECT)

    date_from = models.DateField()
    days_count = models.DecimalField(
        max_digits=6, decimal_places=2,
        validators=[MinValueValidator(1)],
        default=1
    )

    # ✅ auto computed
    date_to = models.DateField(blank=True, null=True)

    note = models.CharField(max_length=255, blank=True)

    # computed
    excess_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_from"]

    def __str__(self):
        return f"{self.employee} {self.leave_type} {self.date_from}"

    def compute_date_to(self):
        """
        MVP: days_count should be whole days (1,2,3...)
        If later you want half-days, we can handle that.
        """
        days_int = int(self.days_count)
        self.date_to = self.date_from + dt.timedelta(days=days_int - 1)

    @transaction.atomic
    def apply_balance(self):
        # ✅ Jalali year for yearly balance
        jalali_year = jdatetime.date.fromgregorian(date=self.date_from).year

        bal, _ = LeaveYearBalance.objects.select_for_update().get_or_create(
            employee=self.employee,
            year=jalali_year,
            leave_type=self.leave_type,
            defaults={"remaining_days": self.leave_type.yearly_limit_days},
        )

        take = min(bal.remaining_days, self.days_count)
        excess = self.days_count - take

        bal.remaining_days = bal.remaining_days - take
        bal.save(update_fields=["remaining_days"])

        self.excess_days = excess

    @transaction.atomic
    def sync_attendance(self):
        """
        Create AttendanceDay=LEAVE for all days in the leave.
        Also remove old leave marks (if entry updated).
        Enforce: Fridays are not stored in attendance.
        """
        # remove previous leave marks for this entry range (safe approach)
        if self.date_to:
            AttendanceDay.objects.filter(
                employee=self.employee,
                date__range=(self.date_from, self.date_to),
                status=AttendanceDay.Status.LEAVE
            ).delete()

        days_int = int(self.days_count)
        for i in range(days_int):
            g_date = self.date_from + dt.timedelta(days=i)

            # ✅ Friday enforcement: do not store anything on Fridays
            if g_date.weekday() == 4:
                continue

            # store leave as exception so it shows in grids/exports
            AttendanceDay.objects.update_or_create(
                employee=self.employee,
                date=g_date,
                defaults={"status": AttendanceDay.Status.LEAVE, "note": f"Leave: {self.leave_type.name}"},
            )

    def save(self, *args, **kwargs):
        # Always compute date_to before saving
        self.compute_date_to()
        super().save(*args, **kwargs)