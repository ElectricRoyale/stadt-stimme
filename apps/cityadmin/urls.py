from django.urls import path

from apps.cityadmin import views

app_name = "cityadmin"

urlpatterns = [
    path("", views.index, name="index"),
    path("vorschlaege/<int:pk>/", views.decide, name="decide"),
    path("stichtag.csv", views.snapshot, name="snapshot"),
    path("einrichtungen/<int:pk>/erledigt/", views.facility_done, name="facility_done"),
    path("einrichtungen/<int:pk>/wieder-oeffnen/", views.facility_reopen, name="facility_reopen"),
]
