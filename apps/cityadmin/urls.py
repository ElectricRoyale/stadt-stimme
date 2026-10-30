from django.urls import path

from apps.cityadmin import views

app_name = "cityadmin"

urlpatterns = [
    path("", views.index, name="index"),
    path("vorschlaege/<int:pk>/", views.decide, name="decide"),
]
