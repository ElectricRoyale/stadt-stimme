from django.urls import path

from apps.reporting import views

app_name = "reporting"

urlpatterns = [
    path("uebersicht/", views.overview, name="overview"),
    path("ergebnisse/", views.results, name="results"),
    path("ergebnisse/tabelle.csv", views.results_table, name="results_table"),
]
