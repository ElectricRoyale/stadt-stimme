from django.urls import path

from apps.proposals import views

app_name = "proposals"

urlpatterns = [
    path("", views.index, name="index"),
    path("aehnlich/", views.similar, name="similar"),
    path("<int:pk>/unterstuetzen/", views.support, name="support"),
]
