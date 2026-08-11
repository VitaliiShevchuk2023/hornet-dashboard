from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.map_view, name="map"),
    path("api/observations.geojson", views.observations_geojson, name="observations-geojson"),
    path("api/state-counts/", views.state_counts_partial, name="state-counts"),
]
