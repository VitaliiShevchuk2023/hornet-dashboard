from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.overview, name="overview"),                       # Q1/Q2
    path("api/observations.geojson", views.observations_geojson, name="observations-geojson"),
    path("habitat/", views.habitat, name="habitat"),                 # Q3
    path("protected-areas/", views.protected_areas, name="protected-areas"),  # Q4
    path("urban-rural/", views.urban_rural, name="urban-rural"),     # Q5
    path("climate/", views.climate, name="climate"),                 # Q6
]
