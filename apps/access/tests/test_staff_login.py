import pytest
from django.contrib.auth.models import User
from django.test import Client
from pytest_django.fixtures import Settings

from apps.access.models import FailedAttempt

pytestmark = pytest.mark.django_db
URL = "/zugang/stadt/"


@pytest.fixture
def demo(settings: Settings) -> None:
    settings.DEMO_MODE = True
    settings.ROOT_URLCONF = "apps.access.tests.urls_with_admin"


@pytest.fixture
def staff() -> User:
    return User.objects.create_user("verwaltung", password="geheim-123", is_staff=True)


def test_both_roles_are_offered(client: Client) -> None:
    content = client.get("/zugang/").content.decode()

    assert 'aria-label="Anmelden als"' in content
    assert 'href="/zugang/" aria-current="page">Bürgerin oder Bürger' in content
    assert 'href="/zugang/stadt/">Stadtverwaltung' in content


def test_without_demo_mode_city_login_is_not_offered(client: Client) -> None:
    content = client.get(URL).content.decode()

    assert "noch nicht freigeschaltet" in content
    assert 'type="password"' not in content
    assert client.post(URL, {"username": "x", "password": "y"}).status_code == 200


@pytest.mark.usefixtures("demo")
def test_staff_logs_in_to_admin(client: Client, staff: User) -> None:
    response = client.post(URL, {"username": "verwaltung", "password": "geheim-123"})

    assert response["Location"] == "/admin/"
    assert client.get(URL)["Location"] == "/admin/"


@pytest.mark.usefixtures("demo")
@pytest.mark.parametrize("password", ["falsch", "geheim-123"])
def test_wrong_password_or_non_staff_is_rejected(
    client: Client, staff: User, password: str
) -> None:
    if password == "geheim-123":
        staff.is_staff = False
        staff.save()

    response = client.post(URL, {"username": "verwaltung", "password": password})

    assert "Benutzername oder Passwort stimmt nicht." in response.content.decode()
    assert FailedAttempt.objects.count() == 1


@pytest.mark.usefixtures("demo")
def test_lockout_applies(client: Client, staff: User, settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 2
    for _ in range(2):
        client.post(URL, {"username": "verwaltung", "password": "falsch"})

    response = client.post(URL, {"username": "verwaltung", "password": "geheim-123"})

    assert response.status_code == 429
