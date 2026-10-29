from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Expenditure, ExpenditureKind
from apps.points.services import Target, points_of, save_distribution
from apps.points.tests.conftest import Catalog

pytestmark = pytest.mark.django_db
URL = "/verteilen/"


def test_requires_login(client: Client) -> None:
    response = client.get(URL)

    assert response.status_code == 302
    assert response["Location"] == "/zugang/"


def test_shows_themes_with_general_row_and_facilities(logged_in: Client, catalog: Catalog) -> None:
    content = logged_in.get(URL).content.decode()

    assert "Sport allgemein" in content
    assert "Hallenbad" in content
    assert "Grundschule" in content
    assert f'name="c-{catalog.sport.pk}"' in content
    assert f'name="f-{catalog.bad.pk}"' in content
    assert 'aria-label="Punkte für Hallenbad"' in content
    assert "<strong data-remaining>100</strong>" in content  # alle Punkte frei
    assert "Noch nichts gespeichert." in content


def test_shows_current_points(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 35})

    content = logged_in.get(URL).content.decode()

    assert 'value="35"' in content
    assert "<strong data-remaining>65</strong>" in content
    assert "Zuletzt gespeichert am" in content


def test_post_saves_and_redirects(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "40", f"c-{catalog.sport.pk}": "10"})

    assert response.status_code == 302
    assert points_of(participant) == {
        Target("f", catalog.bad.pk): 40,
        Target("c", catalog.sport.pk): 10,
    }
    assert "Deine Verteilung ist gespeichert." in logged_in.get(URL).content.decode()


def test_post_over_budget_shows_error_and_keeps_old_state(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 5})

    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "70", f"f-{catalog.schule.pk}": "40"})

    content = response.content.decode()
    assert response.status_code == 422
    assert 'role="alert"' in content
    assert "110 Punkte verteilt" in content
    assert points_of(participant) == {Target("f", catalog.bad.pk): 5}


def test_post_rejects_negative_numbers(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "-3"})

    assert response.status_code == 422
    assert 'aria-invalid="true"' in response.content.decode()


def test_unknown_targets_are_ignored(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, {"f-999999": "50", f"f-{catalog.bad.pk}": "5"})

    assert response.status_code == 302
    assert points_of(participant) == {Target("f", catalog.bad.pk): 5}


def test_shows_spending_of_last_closed_year(logged_in: Client, catalog: Catalog) -> None:
    year = timezone.localdate().year - 1
    for facility, amount in [(catalog.bad, "300000"), (catalog.schule, "100000")]:
        Expenditure.objects.create(
            facility=facility,
            fiscal_year=year,
            amount=Decimal(amount),
            kind=ExpenditureKind.ACTUAL,
            source="Test",
            as_of=date(year, 12, 31),
        )

    content = logged_in.get(URL).content.decode()

    assert f"Ausgaben {year}: 300.000 € (75,0 %)" in content
    assert f"Ausgaben {year}: 75 %" in content  # Thema Sport
    assert f"Im Haushalt {year}" not in content  # noch keine Punkte, kein Hinweis


def test_map_data_lists_only_located_facilities(logged_in: Client, catalog: Catalog) -> None:
    catalog.bad.latitude = Decimal("49.48")
    catalog.bad.longitude = Decimal("8.46")
    catalog.bad.save()

    content = logged_in.get(URL).content.decode()

    assert '"name": "Hallenbad"' in content
    assert '"name": "Grundschule"' not in content
