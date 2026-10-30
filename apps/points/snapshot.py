"""Stichtagswerte aus dem Ereignis-Log (ADR-005, ADR-027, M7).

Punkte und Unterstützer je Ziel, wie sie zu einem Zeitpunkt standen. Reproduzierbar, weil das
Log nie geändert wird. Verfallene Punkte zählen ab dem Lauf von ``expire_points`` nicht mehr
mit (täglich), also mit höchstens einem Tag Verzug gegenüber den Ergebnissen.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from django.db.models import Sum

from apps.points.models import PointEvent
from apps.points.targets import Target


@dataclass
class Tally:
    points: int = 0
    supporters: int = 0


def tally_at(moment: datetime) -> dict[Target, Tally]:
    """Summe der Ereignisse bis einschließlich ``moment``; Ziele ohne Punkte fehlen."""
    nets = (
        PointEvent.objects.filter(created_at__lte=moment)
        .values("participant_id", "facility_id", "category_id")
        .annotate(net=Sum("delta"))
        .filter(net__gt=0)
        .order_by()
    )
    tallies: dict[Target, Tally] = defaultdict(Tally)
    for row in nets:
        facility_id, category_id = row["facility_id"], row["category_id"]
        target = Target("f", facility_id) if facility_id is not None else Target("c", category_id)
        tallies[target].points += row["net"]
        tallies[target].supporters += 1
    return dict(tallies)
