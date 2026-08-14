from django.contrib.gis.db import models


class Species(models.Model):
    label = models.CharField(max_length=64, unique=True)   # "European hornet" / "Asian hornet"
    scientific_name = models.CharField(max_length=128)      # "Vespa crabro" / "Vespa velutina"
    color_hex = models.CharField(max_length=7, default="#999999")

    def __str__(self) -> str:
        return self.label


class Observation(models.Model):
    """
    Team Dashboard track.
    Populated exclusively by `manage.py load_dashboard_csv` from Theresa's
    finalized November CSV handover — NOT by any scheduled/cron job.
    """
    SIGHTING = "sighting"
    NEST = "nest"
    OBSERVATION_TYPE_CHOICES = [
        (SIGHTING, "Sighting"),
        (NEST, "Nest"),
    ]

    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="observations")
    observation_type = models.CharField(
        max_length=16, choices=OBSERVATION_TYPE_CHOICES, default=SIGHTING,
        help_text="Derived from NABU's 'Beobachtung' field (e.g. 'am/im Nest' -> nest, "
                   "everything else -> sighting). Matches the mockup's ART/TYP: Nest filter.",
    )
    location = models.PointField(geography=True, srid=4326, null=True, blank=True)
    bundesland = models.CharField(max_length=128, blank=True)
    landkreis = models.CharField(max_length=128, blank=True)
    locality = models.CharField(max_length=255, blank=True)
    event_date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    basis_of_record = models.CharField(max_length=64, blank=True)
    photo_verified = models.BooleanField(
        default=False,
        help_text="True if basisOfRecord=HUMAN_OBSERVATION and media/photo present "
                   "(Theresa's recommended 'safe way' filter).",
    )
    gbif_id = models.CharField(max_length=64, blank=True, db_index=True)
    source_import = models.CharField(
        max_length=255, blank=True,
        help_text="Filename of the CSV batch this row came from, for traceability.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["species", "year"]),
            models.Index(fields=["bundesland"]),
            models.Index(fields=["observation_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.species.label} @ {self.bundesland or '?'} ({self.year})"
