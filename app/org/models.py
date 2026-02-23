from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    has_head = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="positions")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("department", "name")
        ordering = ["department__name", "name"]

    def __str__(self):
        return f"{self.department} — {self.name}"