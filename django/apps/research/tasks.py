"""
Research track only. This is the ONE scheduled job in the whole project
(see config/settings.py CELERY_BEAT_SCHEDULE) — Dashboard intentionally
has none.
"""
import ast
import logging

from celery import shared_task
from django.contrib.gis.geos import Point
from pygbif import occurrences as occ
from pygbif import species as gbif_species

from .models import GbifObservation

logger = logging.getLogger(__name__)

SPECIES_MAP = {
    "European hornet": "Vespa crabro",
    "Asian hornet": "Vespa velutina",
}


def _safe_gadm(gadm_field, level: str) -> str:
    try:
        if isinstance(gadm_field, dict):
            return gadm_field.get(level, {}).get("name", "")
        d = ast.literal_eval(str(gadm_field))
        return d.get(level, {}).get("name", "")
    except Exception:
        return ""


@shared_task(name="apps.research.tasks.pull_gbif_observations")
def pull_gbif_observations(country: str = "DE", limit_per_page: int = 300) -> dict:
    """
    Weekly pull mirroring NABU|naturgucker -> GBIF upload cadence (Theresa Q&A).
    Upserts by gbif_id so re-runs are idempotent.
    """
    totals = {}
    for label, sci_name in SPECIES_MAP.items():
        result = gbif_species.name_suggest(q=sci_name)
        if not result:
            logger.warning("No GBIF species match for %s", sci_name)
            continue
        key = result[0]["key"]

        offset, created, updated = 0, 0, 0
        while True:
            res = occ.search(taxonKey=key, country=country, limit=limit_per_page, offset=offset)
            batch = res.get("results", [])
            if not batch:
                break

            for rec in batch:
                gbif_id = str(rec.get("gbifID") or rec.get("key"))
                if not gbif_id:
                    continue

                lat, lon = rec.get("decimalLatitude"), rec.get("decimalLongitude")
                point = Point(lon, lat, srid=4326) if lat and lon else None

                has_media = bool(rec.get("media"))
                basis = rec.get("basisOfRecord", "")

                obj, was_created = GbifObservation.objects.update_or_create(
                    gbif_id=gbif_id,
                    defaults=dict(
                        species_label=label,
                        scientific_name=sci_name,
                        location=point,
                        event_date=rec.get("eventDate", "")[:10] or None,
                        year=rec.get("year"),
                        month=rec.get("month"),
                        country=country,
                        state_province=rec.get("stateProvince", "") or "",
                        bundesland_gadm=_safe_gadm(rec.get("gadm"), "level1"),
                        landkreis_gadm=_safe_gadm(rec.get("gadm"), "level2"),
                        locality=rec.get("locality", "") or "",
                        basis_of_record=basis,
                        has_media=has_media,
                        photo_verified=(basis == "HUMAN_OBSERVATION" and has_media),
                        raw_payload=rec,
                    ),
                )
                created += int(was_created)
                updated += int(not was_created)

            offset += len(batch)
            if offset >= res.get("count", 0):
                break

        totals[label] = {"created": created, "updated": updated}
        logger.info("GBIF pull %s: %s", label, totals[label])

    return totals
