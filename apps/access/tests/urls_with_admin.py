"""URLs wie im Demo-Modus, mit Admin und Verwaltungsseite."""

from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from config.urls import urlpatterns as base

urlpatterns: list[URLPattern | URLResolver] = [
    *base,
    path("admin/", admin.site.urls),
    path("verwaltung/", include("apps.cityadmin.urls")),
]
