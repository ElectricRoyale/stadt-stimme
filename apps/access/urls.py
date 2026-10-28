from django.urls import path

from apps.access import views

app_name = "access"

urlpatterns = [
    path("", views.redeem, name="redeem"),
    path("mein-bereich/", views.account, name="account"),
    path("abmelden/", views.logout, name="logout"),
]
