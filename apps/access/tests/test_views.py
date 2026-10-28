import pytest
from django.test import Client
from pytest_django.fixtures import Settings

from apps.access.codes import format_code
from apps.access.services import IssuedCode
from apps.access.session import SESSION_KEY

pytestmark = pytest.mark.django_db


def test_redeem_page_renders_accessible_form(client: Client) -> None:
    content = client.get("/zugang/").content.decode()

    assert '<label for="id_code">' in content
    assert 'aria-describedby="code-hinweis"' in content
    assert 'autocomplete="off"' in content


def test_redeem_page_follows_login_sketch(client: Client, settings: Settings) -> None:
    settings.CITY_NAME = "Beispielstadt"

    content = client.get("/zugang/").content.decode()

    assert "Deine Stimme für Beispielstadt." in content
    assert '<details class="code-help">' in content
    assert 'id="code-zaehler"' in content
    assert "Code aus dem QR-Code übernommen" not in content


def test_qr_link_prefills_code_without_logging_in(client: Client, issued: IssuedCode) -> None:
    response = client.get(f"/zugang/?code={issued.code}")

    content = response.content.decode()
    assert issued.code in content
    assert "Code aus dem QR-Code übernommen" in content
    assert SESSION_KEY not in client.session


def test_valid_code_logs_in_and_redirects(client: Client, issued: IssuedCode) -> None:
    response = client.post("/zugang/", {"code": format_code(issued.code)})

    assert response.status_code == 302
    assert response["Location"] == "/zugang/mein-bereich/"
    assert "Mein Bereich" in client.get("/zugang/mein-bereich/").content.decode()


def test_login_rotates_session_key(client: Client, issued: IssuedCode) -> None:
    client.get("/zugang/")
    session = client.session
    session["vorher"] = True
    session.save()
    before = session.session_key

    client.post("/zugang/", {"code": issued.code})

    assert client.session.session_key != before


def test_wrong_code_shows_message(client: Client) -> None:
    response = client.post("/zugang/", {"code": "ABCD-EFGH-JKMN-PQRS"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Diesen Code kennen wir nicht" in content
    assert 'aria-invalid="true"' in content
    assert 'role="alert"' in content
    assert "Code aus dem QR-Code übernommen" not in content


def test_lockout_returns_429(client: Client, issued: IssuedCode, settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 2
    for _ in range(2):
        client.post("/zugang/", {"code": "ABCD-EFGH-JKMN-PQRS"})

    response = client.post("/zugang/", {"code": issued.code})

    assert response.status_code == 429
    assert "Zu viele Fehlversuche" in response.content.decode()


def test_account_requires_session(client: Client) -> None:
    response = client.get("/zugang/mein-bereich/")

    assert response.status_code == 302
    assert response["Location"] == "/zugang/"


def test_logged_in_user_skips_form(client: Client, issued: IssuedCode) -> None:
    client.post("/zugang/", {"code": issued.code})

    assert client.get("/zugang/")["Location"] == "/zugang/mein-bereich/"


def test_logout_ends_session(client: Client, issued: IssuedCode) -> None:
    client.post("/zugang/", {"code": issued.code})

    response = client.post("/zugang/abmelden/")

    assert response.status_code == 302
    assert client.get("/zugang/mein-bereich/").status_code == 302


def test_logout_requires_post(client: Client) -> None:
    assert client.get("/zugang/abmelden/").status_code == 405


def test_home_leads_to_account_when_logged_in(client: Client, issued: IssuedCode) -> None:
    client.post("/zugang/", {"code": issued.code})

    assert client.get("/")["Location"] == "/zugang/mein-bereich/"
    assert "Abmelden" in client.get("/zugang/mein-bereich/").content.decode()
