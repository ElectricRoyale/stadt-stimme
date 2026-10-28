from collections.abc import Callable

from django.test import Client


def test_admin_is_unreachable_without_demo_mode(
    client: Client, demo_mode: Callable[[bool], None]
) -> None:
    demo_mode(False)

    assert client.get("/admin/").status_code == 404


def test_admin_is_reachable_in_demo_mode(client: Client, demo_mode: Callable[[bool], None]) -> None:
    demo_mode(True)

    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
