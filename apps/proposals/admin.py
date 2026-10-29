from typing import Any

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.db.models.functions import Coalesce
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from apps.proposals.models import Proposal, ProposalStatus

DECIDED = (ProposalStatus.ACCEPTED, ProposalStatus.REJECTED)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Die Verwaltung prüft, gibt frei und entscheidet (ADR-016). Inhalte kommen von Bürgern."""

    list_display = ["number", "title", "category", "facility", "status", "supports", "created_at"]
    list_filter = ["status", "category"]
    search_fields = ["title", "text"]
    fields = [
        "participant",
        "title",
        "text",
        "category",
        "facility",
        "created_at",
        "status",
        "published_at",
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
        "created_at",
        "published_at",
        "decided_at",
    ]
    autocomplete_fields = ["measure"]
    actions = ["publish", "accept", "reject"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Proposal]:
        queryset: QuerySet[Proposal] = super().get_queryset(request)
        return queryset.annotate(support_count=Count("supports"))

    @admin.display(description="Nummer", ordering="pk")
    def number(self, obj: Proposal) -> str:
        return obj.number

    @admin.display(description="Unterstützungen", ordering="support_count")
    def supports(self, obj: Proposal) -> int:
        return int(getattr(obj, "support_count", 0))

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def save_model(
        self, request: HttpRequest, obj: Proposal, form: ModelForm, change: bool
    ) -> None:
        stamp_dates(obj)
        super().save_model(request, obj, form, change)

    @admin.action(description="Freigeben", permissions=["change"])
    def publish(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        queryset.update(
            status=ProposalStatus.PUBLISHED,
            published_at=Coalesce("published_at", timezone.now()),
        )

    @admin.action(description="Annehmen", permissions=["change"])
    def accept(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        _decide(queryset, ProposalStatus.ACCEPTED)

    @admin.action(description="Ablehnen", permissions=["change"])
    def reject(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        _decide(queryset, ProposalStatus.REJECTED)


def stamp_dates(proposal: Proposal) -> None:
    """Freigabe- und Entscheidungsdatum aus dem Status, beim ersten Erreichen gesetzt."""
    now = timezone.now()
    if proposal.status == ProposalStatus.PUBLISHED and proposal.published_at is None:
        proposal.published_at = now
    if proposal.status in DECIDED and proposal.decided_at is None:
        proposal.decided_at = now


def _decide(queryset: QuerySet[Proposal], status: str) -> None:
    changes: dict[str, Any] = {
        "status": status,
        "decided_at": Coalesce("decided_at", timezone.now()),
    }
    queryset.update(**changes)
