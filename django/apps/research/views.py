from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from .models import GbifObservation

# Q3/Q4/Q5 keyword proxies — ported as-is from utils/gbif_loader.py & pages/*.py
HABITAT_KEYWORDS = {
    "Forest / Wald": ["wald", "forst", "forest", "gehölz", "baum"],
    "Field / Feld": ["feld", "flur", "wiese", "meadow", "field"],
    "Garden / Garten": ["garten", "garden", "park", "grün"],
    "Settlement": ["stadt", "dorf", "ortschaft", "siedlung", "urban"],
    "Water / Wasser": ["bach", "fluss", "see", "teich", "wasser", "river"],
    "Moor / Sumpf": ["moor", "sumpf", "feucht", "wetland"],
    "Vineyard": ["weinberg", "reben", "vineyard"],
}
PROTECTED_KEYWORDS = [
    "naturschutz", "schutzgebiet", "nationalpark", "national park",
    "naturpark", "biosphäre", "biosphere", "reservat", "reserve",
    "vogelschutz", "ffh", "natura 2000", "naturreservat",
]


def overview(request):
    """Q1/Q2 — species overlap + European hornet distribution."""
    qs = GbifObservation.objects.filter(location__isnull=False)
    return render(request, "research/overview.html", {
        "total": qs.count(),
        "by_species": qs.values("species_label").annotate(n=Count("id")),
    })


def observations_geojson(request):
    qs = GbifObservation.objects.filter(location__isnull=False)
    species = request.GET.get("species")
    if species:
        qs = qs.filter(species_label=species)
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [o.location.x, o.location.y]},
            "properties": {
                "species": o.species_label,
                "year": o.year,
                "bundesland": o.bundesland_gadm,
                "photo_verified": o.photo_verified,
            },
        }
        for o in qs[:5000]
    ]
    return JsonResponse({"type": "FeatureCollection", "features": features})


def habitat(request):
    """Q3 — locality-keyword habitat proxy (known technical debt, not a real spatial join)."""
    qs = GbifObservation.objects.exclude(locality="")

    def classify(locality: str) -> str:
        loc = locality.lower()
        for habitat_name, kws in HABITAT_KEYWORDS.items():
            if any(kw in loc for kw in kws):
                return habitat_name
        return "Other"

    counts = {}
    for loc in qs.values_list("locality", flat=True):
        h = classify(loc)
        counts[h] = counts.get(h, 0) + 1

    return render(request, "research/habitat.html", {"counts": counts})


def protected_areas(request):
    """Q4 — low priority per Theresa; kept for completeness."""
    qs = GbifObservation.objects.exclude(locality="")
    protected = sum(
        1 for loc in qs.values_list("locality", flat=True)
        if any(kw in loc.lower() for kw in PROTECTED_KEYWORDS)
    )
    return render(request, "research/protected_areas.html", {
        "protected": protected,
        "total": qs.count(),
    })


def urban_rural(request):
    """Q5 — synanthropic behavior. Placeholder parity with pages/4_Urban_Rural.py (was empty)."""
    return render(request, "research/urban_rural.html", {})


def climate(request):
    """Q6 — low priority per Theresa; weather correlation."""
    return render(request, "research/climate.html", {})
