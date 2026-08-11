from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from .models import Observation, Species


def map_view(request):
    """Public-facing dashboard page (Leaflet map + HTMX filter bar)."""
    context = {
        "species_list": Species.objects.all(),
        "year_min": Observation.objects.order_by("year").values_list("year", flat=True).first() or 2020,
        "year_max": Observation.objects.order_by("-year").values_list("year", flat=True).first() or 2026,
    }
    return render(request, "dashboard/map.html", context)


def observations_geojson(request):
    """
    HTMX/Leaflet fetches this as GeoJSON. Filters: species, year, verified_only.
    Photo-verified filter defaults to ON for public output (Theresa's recommendation).
    """
    qs = Observation.objects.select_related("species").filter(location__isnull=False)

    species = request.GET.get("species")
    if species:
        qs = qs.filter(species__label=species)

    year = request.GET.get("year")
    if year:
        qs = qs.filter(year=year)

    verified_only = request.GET.get("verified_only", "true") == "true"
    if verified_only:
        qs = qs.filter(photo_verified=True)

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [obs.location.x, obs.location.y],
            },
            "properties": {
                "species": obs.species.label,
                "color": obs.species.color_hex,
                "year": obs.year,
                "bundesland": obs.bundesland,
                "photo_verified": obs.photo_verified,
            },
        }
        for obs in qs[:5000]  # sane cap for map payload
    ]
    return JsonResponse({"type": "FeatureCollection", "features": features})


def state_counts_partial(request):
    """HTMX partial: federal-state observation counts table."""
    counts = (
        Observation.objects.filter(photo_verified=True)
        .values("bundesland", "species__label")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return render(request, "dashboard/_state_counts.html", {"counts": counts})
