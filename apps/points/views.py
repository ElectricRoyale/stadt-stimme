"""Punkte verteilen: alle Themen und Einrichtungen auf einer Seite, gespeichert in einem Schritt."""

from dataclasses import dataclass

from django.contrib import messages
from django.forms import BoundField
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.access.models import Participant
from apps.access.views import participant_required
from apps.points.forms import DistributionForm
from apps.points.models import POINTS_BUDGET
from apps.points.overview import Group, Row, build_groups
from apps.points.services import BudgetExceededError, points_of, save_distribution


@dataclass(frozen=True)
class RowView:
    row: Row
    field: BoundField


@dataclass(frozen=True)
class GroupView:
    group: Group
    rows: list[RowView]


@require_http_methods(["GET", "POST"])
@participant_required
def distribute(request: HttpRequest, participant: Participant) -> HttpResponse:
    groups = build_groups(points_of(participant))
    targets = [row.target for group in groups for row in group.rows]

    if request.method == "POST":
        form = DistributionForm(targets, request.POST)
        if form.is_valid():
            try:
                save_distribution(participant, form.points())
            except BudgetExceededError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, "Deine Verteilung ist gespeichert.")
                return redirect("points:distribute")
    else:
        form = DistributionForm(targets, initial=_initial(groups))

    used = sum(g.points for g in groups)
    return render(
        request,
        "points/distribute.html",
        {
            "form": form,
            "groups": [
                GroupView(g, [RowView(r, form[r.target.key]) for r in g.rows]) for g in groups
            ],
            "budget": POINTS_BUDGET,
            "used": used,
            "remaining": POINTS_BUDGET - used,
        },
        status=200 if not form.is_bound or form.is_valid() else 422,
    )


def _initial(groups: list[Group]) -> dict[str, int]:
    return {row.target.key: row.points for group in groups for row in group.rows}
