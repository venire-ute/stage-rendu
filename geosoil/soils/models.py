# Standard Django model imports
from django.db import models
from django.contrib.gis.db import models as gis_models



class Source(models.Model):
    """Represents a source of soil profile data."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True, null=True, help_text="Link to the source")


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def profile_count(self) -> int:
        """Returns the number of soil profiles linked to this source."""
        return self.soil_profiles.count()

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name

class SoilProfile(models.Model):
    """Basic representation of a soil profile."""

    profile_id = models.CharField(max_length=100, )#unique=True
    code = models.CharField(max_length=255,unique=True,)
    location = gis_models.PointField(help_text="Geographic location of the profile")
    description = models.TextField(blank=True)
    source = models.ForeignKey(
        Source,
        on_delete=models.SET_NULL,
        # blank=True,
        null=True,
        help_text="Source of the profile data",
        related_name="soil_profiles",
    )
    date_de_prelevement = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date of sampling",
    )
    pays = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country where the profile is located",
    )
    teledection_data  = models.JSONField(default=dict, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    class Meta:
        unique_together = ('location', 'source')

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.profile_id


class Layer(models.Model):
    """Represents an individual soil layer within a profile."""
    

    profile = models.ForeignKey(
        SoilProfile,
        on_delete=models.CASCADE,
        related_name="layers",
    )
    name = models.CharField(max_length=100)
    depth_top = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Top depth in centimeters",
    )
    depth_bottom = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Bottom depth in centimeters",
    )
    description = models.TextField(blank=True)

    carbon_content = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Carbon content in gt/ha",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  
        return f"{self.name} ({self.profile.profile_id})"


class Property(models.Model):
    """Flexible attribute linked to a soil profile."""
    PF='PF' 
    LY='LY' 
  
    type = (
    (PF, 'profil'),
    (LY, 'couche'),

    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)  
    description = models.TextField(blank=True)

    disable = models.BooleanField(
        default=False,
        help_text="Disable this property, it will not be used in the profile or layer",
    )

    property_type = models.CharField(
        max_length=2,
        choices=type,
        default=PF,
        help_text="Type of property: PF for profile, LY for layer",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  
        return f"{self.name}: {self.value}"
    

class ProfileProperty(models.Model):
    """Flexible attribute linked to a soil profile."""

    profile = models.ForeignKey(
        SoilProfile,
        on_delete=models.CASCADE,
        related_name="properties",
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="profile_properties",
    )
    
    
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)  
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        unique_together = ('profile', 'property')

    def __str__(self) -> str:  
        return f"{self.name}: {self.value}"


class LayerProperty(models.Model):
    """Flexible attribute linked to a soil layer."""

    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="properties",
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str: 
        return f"{self.name}: {self.value}"


