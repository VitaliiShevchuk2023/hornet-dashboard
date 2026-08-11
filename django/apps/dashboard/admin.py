from django.contrib import admin

from .models import Observation, Species


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("label", "scientific_name", "color_hex")


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("species", "bundesland", "year", "photo_verified", "source_import")
    list_filter = ("species", "photo_verified", "year", "bundesland")
    search_fields = ("locality", "gbif_id")
