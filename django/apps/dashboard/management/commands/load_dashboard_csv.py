"""
Load Theresa's finalized November CSV into the Dashboard track.

Usage:
    python manage.py load_dashboard_csv path/to/Data_NABU_Hornet_Campaign_2025.xlsx --sheet 0

This is intentionally a MANUAL, one-shot command — not a Celery task.
Per the David directive: Team Dashboard needs no cron jobs, since a single
finalized handover file replaces continuous API polling.

NOTE: NABU's Excel schema is German-language with proprietary regional codes
(Provinz: SHHH, MeVo, NiHB, ...) and is NOT Darwin Core / GBIF-compatible.
This command expects a normalized CSV (species, lat, lon, date, bundesland,
photo_verified, gbif_id) — run it through utils/naturgucker_loader.py-style
normalization first if you're feeding it the raw NABU Excel export directly.
"""
import csv
from datetime import datetime

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from apps.dashboard.models import Observation, Species

REQUIRED_COLUMNS = {"species", "lat", "lon", "bundesland"}


class Command(BaseCommand):
    help = "One-off import of Theresa's finalized CSV into the Dashboard track (no cron)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse and validate only, don't write to the database.",
        )

    def handle(self, *args, **options):
        path = options["csv_path"]
        dry_run = options["dry_run"]

        try:
            f = open(path, newline="", encoding="utf-8")
        except OSError as e:
            raise CommandError(f"Cannot open {path}: {e}")

        with f:
            reader = csv.DictReader(f)
            if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
                raise CommandError(
                    f"CSV missing required columns {REQUIRED_COLUMNS}. "
                    f"Found: {reader.fieldnames}"
                )

            created, skipped = 0, 0
            for row in reader:
                species, _ = Species.objects.get_or_create(
                    label=row["species"].strip(),
                    defaults={"scientific_name": row.get("scientific_name", "")},
                )

                lat, lon = row.get("lat"), row.get("lon")
                point = None
                if lat and lon:
                    try:
                        point = Point(float(lon), float(lat), srid=4326)
                    except ValueError:
                        point = None

                event_date = None
                if row.get("event_date"):
                    try:
                        event_date = datetime.strptime(row["event_date"], "%Y-%m-%d").date()
                    except ValueError:
                        pass

                if dry_run:
                    created += 1
                    continue

                Observation.objects.create(
                    species=species,
                    location=point,
                    bundesland=row.get("bundesland", "").strip(),
                    landkreis=row.get("landkreis", "").strip(),
                    locality=row.get("locality", "").strip(),
                    event_date=event_date,
                    year=event_date.year if event_date else row.get("year") or None,
                    month=event_date.month if event_date else None,
                    basis_of_record=row.get("basis_of_record", ""),
                    photo_verified=str(row.get("photo_verified", "")).lower() in ("true", "1", "yes"),
                    gbif_id=row.get("gbif_id", ""),
                    source_import=path.split("/")[-1],
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(
                f"{'[dry-run] ' if dry_run else ''}Processed {created} rows from {path} "
                f"({skipped} skipped)."
            ))
