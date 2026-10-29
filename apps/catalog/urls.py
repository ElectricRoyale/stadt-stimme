from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.search_page, name="search"),
]
