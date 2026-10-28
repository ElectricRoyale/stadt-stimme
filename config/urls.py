"""URL-Konfiguration. Der Admin ist nur im Demo-Modus erreichbar (Admin-Login zurückgestellt)."""

from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.core.urls")),
]

if settings.DEMO_MODE:
    urlpatterns.append(path("admin/", admin.site.urls))
