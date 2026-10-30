from django.urls import path

from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.settings_page, name="settings"),
    path("entfernen/", views.remove, name="remove"),
    path("bestaetigen/<str:token>/", views.confirm, name="confirm"),
    path("abmelden/<str:token>/", views.unsubscribe, name="unsubscribe"),
]
