from django.urls import path

from apps.points import views

app_name = "points"

urlpatterns = [
    path("", views.distribute, name="distribute"),
]
