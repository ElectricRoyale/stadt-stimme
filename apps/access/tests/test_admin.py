from collections.abc import Callable

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.access.services import IssuedCode

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client_in_demo(client: Client, demo_mode: Callable[[bool], None]) -> Client:
    demo_mode(True)
    user = get_user_model().objects.create_superuser("markus", password="test-passwort")
    client.force_login(user)
    return client


def test_codes_are_listed_without_hash(admin_client_in_demo: Client, issued: IssuedCode) -> None:
    response = admin_client_in_demo.get("/admin/access/accesscode/")

    assert response.status_code == 200
    assert "Test" in response.content.decode()


def test_codes_cannot_be_added_in_admin(admin_client_in_demo: Client) -> None:
    assert admin_client_in_demo.get("/admin/access/accesscode/add/").status_code == 403
