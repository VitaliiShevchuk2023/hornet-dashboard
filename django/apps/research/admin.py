from django.contrib import admin

from .models import GbifObservation, ResearchQuestionNote


@admin.register(GbifObservation)
class GbifObservationAdmin(admin.ModelAdmin):
    list_display = ("species_label", "bundesland_gadm", "year", "photo_verified", "fetched_at")
    list_filter = ("species_label", "photo_verified", "year")
    search_fields = ("gbif_id", "locality")


@admin.register(ResearchQuestionNote)
class ResearchQuestionNoteAdmin(admin.ModelAdmin):
    list_display = ("question", "uses_locality_keyword_proxy", "updated_at")
