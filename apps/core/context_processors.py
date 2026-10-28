from django.conf import settings
from django.http import HttpRequest


def city(request: HttpRequest) -> dict[str, str]:
    return {"city_name": settings.CITY_NAME}
