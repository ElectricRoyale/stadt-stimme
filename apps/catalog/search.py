"""Suche über Einrichtungen und Maßnahmen für die Suchleiste oben (ADR-018)."""

from dataclasses import dataclass

from django.db.models import Prefetch, Q

from apps.catalog.models import Facility, Measure

MIN_QUERY_LENGTH = 2
MAX_HITS = 30


@dataclass(frozen=True)
class Hit:
    facility: Facility
    measures: list[Measure]

    @property
    def target_key(self) -> str:
        """Schlüssel wie in Verteilen und Ergebnisse (``f-<pk>``)."""
        return f"f-{self.facility.pk}"


def search(query: str) -> list[Hit]:
    """Einrichtungen, deren Name, Adresse oder Beschreibung passt oder die eine passende
    Maßnahme haben. Passende Maßnahmen stehen dabei; sonst keine."""
    words = query.split()
    if len(query.strip()) < MIN_QUERY_LENGTH:
        return []
    measure_match = Q()
    facility_match = Q()
    for word in words:
        measure_match &= Q(title__icontains=word) | Q(description__icontains=word)
        facility_match &= (
            Q(name__icontains=word)
            | Q(address__icontains=word)
            | Q(description__icontains=word)
            | Q(measures__title__icontains=word)
            | Q(measures__description__icontains=word)
        )
    facilities = (
        Facility.objects.filter(facility_match)
        .distinct()
        .select_related("category")
        .prefetch_related(
            Prefetch("measures", queryset=Measure.objects.filter(measure_match), to_attr="hits")
        )
        .order_by("name")[:MAX_HITS]
    )
    return [Hit(facility=f, measures=f.hits) for f in facilities]
