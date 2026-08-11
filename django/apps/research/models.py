from django.contrib.gis.db import models


class GbifObservation(models.Model):
    """
    Team Research track. Populated continuously by the weekly Celery task
    `pull_gbif_observations` (see tasks.py) — this is the track that keeps
    the "no cron jobs" rule from the Dashboard track; Research explicitly
    still needs it, per the David directive scoping discussion.
    """
    species_label = models.CharField(max_length=64)          # "European hornet" / "Asian hornet"
    scientific_name = models.CharField(max_length=128)
    gbif_id = models.CharField(max_length=64, unique=True, db_index=True)
    location = models.PointField(geography=True, srid=4326, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    country = models.CharField(max_length=8, default="DE")
    state_province = models.CharField(max_length=128, blank=True)   # GBIF stateProvince (sparse)
    bundesland_gadm = models.CharField(max_length=128, blank=True)  # from gadm.level1 (complete)
    landkreis_gadm = models.CharField(max_length=128, blank=True)   # from gadm.level2
    locality = models.CharField(max_length=255, blank=True)
    basis_of_record = models.CharField(max_length=64, blank=True)
    has_media = models.BooleanField(default=False)
    photo_verified = models.BooleanField(
        default=False,
        help_text="basisOfRecord=HUMAN_OBSERVATION and has_media=True",
    )
    raw_payload = models.JSONField(null=True, blank=True, help_text="Full GBIF record, for reprocessing.")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["species_label", "year"]),
            models.Index(fields=["bundesland_gadm"]),
        ]

    def __str__(self) -> str:
        return f"{self.species_label} {self.gbif_id}"


class ResearchQuestionNote(models.Model):
    """
    Lightweight tracking of Q1-Q6 status/methodology notes, so the
    Django admin can double as the research-question dashboard David asked
    about, instead of scattering this across Mural/Slack.
    """
    QUESTION_CHOICES = [
        ("Q1", "Q1 — Displacement (European vs Asian hornet)"),
        ("Q2", "Q2 — European hornet distribution in Germany"),
        ("Q3", "Q3 — Habitat correlation"),
        ("Q4", "Q4 — Protected areas (low priority per Theresa)"),
        ("Q5", "Q5 — Synanthropic / urban-rural behavior"),
        ("Q6", "Q6 — Climate & weather impact (low priority per Theresa)"),
    ]
    question = models.CharField(max_length=2, choices=QUESTION_CHOICES, unique=True)
    methodology_note = models.TextField(blank=True)
    uses_locality_keyword_proxy = models.BooleanField(
        default=False,
        help_text="True for Q3/Q4/Q5 — keyword-parsing of `locality` is a proxy, "
                   "not a real spatial join. Known technical debt.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.get_question_display()
