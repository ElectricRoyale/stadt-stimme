from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.notifications.models import NotificationContact


@admin.register(NotificationContact)
class NotificationContactAdmin(admin.ModelAdmin):
    """Nur Zustand, nie die Adresse: Bürger verwalten sie selbst (ADR-004)."""

    list_display = ["participant", "confirm_sent_at", "confirmed_at", "expiry_warned_at"]
    fields = readonly_fields = (
        "participant",
        "confirm_sent_at",
        "confirmed_at",
        "expiry_warned_at",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
