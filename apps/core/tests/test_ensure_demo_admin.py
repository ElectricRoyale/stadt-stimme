import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from pytest_django.fixtures import Settings


@pytest.mark.django_db
def test_does_nothing_outside_demo_mode(settings: Settings) -> None:
    settings.DEMO_MODE = False

    call_command("ensure_demo_admin")

    assert not get_user_model().objects.exists()


@pytest.mark.django_db
def test_creates_admin_once_in_demo_mode(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.DEMO_MODE = True
    monkeypatch.setenv("DEMO_ADMIN_USERNAME", "demo")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "demo-passwort")

    call_command("ensure_demo_admin")
    call_command("ensure_demo_admin")

    user = get_user_model().objects.get()
    assert user.username == "demo"
    assert user.is_superuser
    assert user.check_password("demo-passwort")


@pytest.mark.django_db
def test_fails_loudly_without_credentials(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.DEMO_MODE = True
    monkeypatch.delenv("DEMO_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)

    with pytest.raises(CommandError):
        call_command("ensure_demo_admin")
