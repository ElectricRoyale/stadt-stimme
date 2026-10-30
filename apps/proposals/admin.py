from typing import Any

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.db.models.functions import Coalesce
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html

from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import after_accept

DECIDED = (ProposalStatus.ACCEPTED, ProposalStatus.REJECTED)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Die Verwaltung entscheidet (ADR-016); eine Freigabe gibt es nicht (ADR-025)."""

    list_display = ["number", "title", "category", "facility", "status", "supports", "created_at"]
    list_filter = ["status", "category"]
    search_fields = ["title", "text"]
    fields = [
        "participant",
        "title",
        "text",
        "category",
        "facility",
        "map_link",
        "created_at",
        "status",
        "decided_at",
        "answer",
        "measure",
    ]
    readonly_fields = [
        "participant",
        "title",
        "text",
        "category",
        "facility",
        "map_link",
        "created_at",
        "decided_at",
    ]
    autocomplete_fields = ["measure"]
    actions = ["accept", "reject"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Proposal]:
        queryset: QuerySet[Proposal] = super().get_queryset(request)
        return queryset.annotate(support_count=Count("supports"))

    @admin.display(description="Nummer", ordering="pk")
    def number(self, obj: Proposal) -> str:
        return obj.number

    @admin.display(description="Unterstützungen", ordering="support_count")
    def supports(self, obj: Proposal) -> int:
        return int(getattr(obj, "support_count", 0))

    @admin.display(description="Neuer Ort")
    def map_link(self, obj: Proposal) -> str:
        if not obj.has_point:
            return "kein neuer Ort"
        lat, lng = obj.latitude, obj.longitude
        return format_html(
            '<a href="https://www.openstreetmap.org/?mlat={}&amp;mlon={}#map=18/{}/{}" '
            'target="_blank" rel="noopener">{}, {} auf der Karte</a>',
            lat,
            lng,
            lat,
            lng,
            lat,
            lng,
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: Proposal, form: ModelForm, change: bool
    ) -> None:
        stamp_dates(obj)
        super().save_model(request, obj, form, change)
        if obj.status == ProposalStatus.ACCEPTED:
            after_accept(obj)

    @admin.action(description="Annehmen", permissions=["change"])
    def accept(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        _decide(queryset, ProposalStatus.ACCEPTED)
        for proposal in queryset.select_related("facility"):
            after_accept(proposal)

    @admin.action(description="Ablehnen", permissions=["change"])
    def reject(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        _decide(queryset, ProposalStatus.REJECTED)


def stamp_dates(proposal: Proposal) -> None:
    """Entscheidungsdatum beim ersten Erreichen von angenommen oder abgelehnt."""
    if proposal.status in DECIDED and proposal.decided_at is None:
        proposal.decided_at = timezone.now()


def _decide(queryset: QuerySet[Proposal], status: str) -> None:
    changes: dict[str, Any] = {
        "status": status,
        "decided_at": Coalesce("decided_at", timezone.now()),
    }
    queryset.update(**changes)
