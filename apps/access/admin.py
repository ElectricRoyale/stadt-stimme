"""Nur lesend: Codes entstehen per ``create_access_codes``, weil der Klartext nur dort
einmal sichtbar ist. Sperren (M6) und Druckexport (M5) sind bis zur Teamabstimmung
zurückgestellt."""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.access.models import AccessCode, Participant


class _ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(AccessCode)
class AccessCodeAdmin(_ReadOnlyAdmin):
    list_display = ["serial", "batch", "status", "created_at", "redeemed_at"]
    list_filter = ["status", "batch"]
    exclude = ["code_hash"]


@admin.register(Participant)
class ParticipantAdmin(_ReadOnlyAdmin):
    list_display = ["__str__", "access_code", "created_at", "last_active_at"]
