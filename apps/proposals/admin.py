from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.proposals.models import Proposal, ProposalStatus


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Die Verwaltung prüft Vorschläge und schaltet sie frei. Inhalte schreiben nur die Bürger."""

    list_display = ["number", "title", "category", "facility", "status", "supports", "created_at"]
    list_filter = ["status", "category"]
    search_fields = ["title", "text"]
    readonly_fields = ["participant", "title", "text", "category", "facility", "created_at"]
    actions = ["publish", "reject"]

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

    @admin.action(description="Freigeben", permissions=["change"])
    def publish(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        queryset.update(status=ProposalStatus.PUBLISHED)

    @admin.action(description="Ablehnen", permissions=["change"])
    def reject(self, request: HttpRequest, queryset: QuerySet[Proposal]) -> None:
        queryset.update(status=ProposalStatus.REJECTED)
