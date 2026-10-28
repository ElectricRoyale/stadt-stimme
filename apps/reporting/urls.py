from django.urls import path

from apps.reporting import views

app_name = "reporting"

urlpatterns = [
    path("", views.overview, name="overview"),
]
