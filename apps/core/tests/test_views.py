from unittest.mock import patch

import pytest
from django.db import OperationalError
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_health_reports_ok_when_database_answers(client: Client) -> None:
    response = client.get(reverse("core:health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_database_is_down(client: Client) -> None:
    with patch("apps.core.views.connection.cursor", side_effect=OperationalError("down")):
        response = client.get(reverse("core:health"))

    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"


def test_health_rejects_post(client: Client) -> None:
    assert client.post(reverse("core:health")).status_code == 405


@pytest.mark.django_db
def test_home_redirects_to_code_entry(client: Client) -> None:
    response = client.get(reverse("core:home"))

    assert response.status_code == 302
    assert response["Location"] == reverse("access:redeem")


@pytest.mark.django_db
def test_pages_are_german_and_mobile_ready(client: Client) -> None:
    response = client.get(reverse("access:redeem"))
    html = response.content.decode()

    assert response.status_code == 200
    assert '<html lang="de">' in html
    assert 'name="viewport"' in html
    assert 'href="#inhalt"' in html
