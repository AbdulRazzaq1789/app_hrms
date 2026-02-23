from django.contrib import admin
from .models import Department, Position

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "has_head")
    search_fields = ("name",)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    list_filter = ("department",)
    search_fields = ("name",)