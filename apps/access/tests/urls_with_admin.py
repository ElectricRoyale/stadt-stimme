"""URLs wie im Demo-Modus, in dem der Admin eingebunden ist."""

from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from config.urls import urlpatterns as base

urlpatterns: list[URLPattern | URLResolver] = [*base, path("admin/", admin.site.urls)]
