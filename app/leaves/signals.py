import datetime as dt
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import LeaveEntry
from attendance.models import AttendanceDay


@receiver(pre_delete, sender=LeaveEntry)
def remove_leave_attendance(sender, instance: LeaveEntry, **kwargs):
    """
    When a LeaveEntry is deleted, remove AttendanceDay rows that were created
    to represent that leave (status=LEAVE) for the same employee and date range.
    """
    # Ensure date_to exists
    date_from = instance.date_from
    date_to = instance.date_to

    if date_from is None:
        return

    # If date_to wasn't saved (edge case), compute it from days_count
    if date_to is None and instance.days_count:
        try:
            days_int = int(instance.days_count)
            date_to = date_from + dt.timedelta(days=days_int - 1)
        except Exception:
            date_to = date_from

    AttendanceDay.objects.filter(
        employee=instance.employee,
        date__range=(date_from, date_to),
        status=AttendanceDay.Status.LEAVE,
    ).delete()