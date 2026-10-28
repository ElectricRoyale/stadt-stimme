import threading

import pytest
from django.db import connection
from pytest_django.fixtures import Settings

from apps.access.models import FailedAttempt
from apps.access.services import redeem_code

PARALLEL_REQUESTS = 12


@pytest.mark.django_db(transaction=True)
def test_parallel_failures_do_not_exceed_limit(settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 3
    start = threading.Barrier(PARALLEL_REQUESTS)

    def attempt() -> None:
        start.wait()
        try:
            redeem_code("ABCD-EFGH-JKMN-PQRS", client="203.0.113.7")
        finally:
            connection.close()

    threads = [threading.Thread(target=attempt) for _ in range(PARALLEL_REQUESTS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert FailedAttempt.objects.count() == 3
