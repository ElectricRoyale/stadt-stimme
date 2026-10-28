from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.points.models import Allocation


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    """Nur lesen: Punkte vergeben ausschließlich die Bürger selbst."""

    list_display = ["participant", "facility", "category", "points", "updated_at"]
    list_filter = ["category", "facility"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
