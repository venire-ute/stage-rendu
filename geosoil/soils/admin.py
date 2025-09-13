from django.contrib import admin

from .models import (
    SoilProfile,
    Layer,
    ProfileProperty,
    LayerProperty,
    Source,
    Property

)


@admin.register(SoilProfile)
class SoilProfileAdmin(admin.ModelAdmin):
    list_display = ("profile_id", "code", "created_at","teledection_data")
    search_fields = ("profile_id","source__name")
    list_filter=("source",)


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ("profile", "name", "depth_top", "depth_bottom")


@admin.register(ProfileProperty)
class ProfilePropertyAdmin(admin.ModelAdmin):
    list_display = ("profile", "name", "value", "unit")


@admin.register(LayerProperty)
class LayerPropertyAdmin(admin.ModelAdmin):
    list_display = ("layer", "name", "value", "unit")


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "url")

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "unit")
    search_fields = ("name",)
    list_filter = ("unit",)
    ordering = ("name",)

    