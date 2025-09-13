# -*- coding: utf-8 -*-
"""
Django management command (and reusable module) to attach Sentinel‑1, Sentinel‑2 ou
Sentinel‑3 pixel values to every **SoilProfile** point stocké dans ta base GeoDjango.

Adapté au modèle que tu viens de partager :

```python
class SoilProfile(models.Model):
    profile_id  = models.CharField(max_length=100)
    code        = models.CharField(max_length=100, blank=True, null=True)
    location    = gis_models.PointField(srid=4326)  # lon/lat WGS‑84
    ...
    teledection_data = JSONField(default=dict, blank=True)  # <‑‑ AJOUT
```

Exécute ensuite :

```bash
python manage.py makemigrations soil && python manage.py migrate
```

Usage côté CLI :

```bash
python manage.py fetch_sentinel_data \
    --start 2024-01-01 --end 2024-12-31 --sensor all
```

Le JSON est enregistré dans « sentinel_data » pour chaque profil.
"""

import datetime as dt
from typing import Dict, Any

import ee  # Google Earth Engine
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from soils.models import SoilProfile  # adapte le chemin si nécessaire

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
# ---------------------------------------------------------------------------
# Earth Engine helpers
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/earthengine.readonly"]

def authenticate_earth_engine():
    
    creds = None

    # Vérifie si token.json existe (authentification précédente)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Sinon, lance le flow OAuth pour obtenir un token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Sauvegarde le token pour les prochaines fois
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Initialisation Earth Engine avec les credentials OAuth
    ee.Initialize(credentials=creds)
    print(" Earth Engine authentifié avec succès !")


def init_ee() -> None:
    """Initialise l'auth Earth Engine (service account ou token local)."""
    if hasattr(settings, "EE_SERVICE_ACCOUNT") and hasattr(settings, "EE_PRIVATE_KEY"):
        credentials = ee.ServiceAccountCredentials(
            settings.EE_SERVICE_ACCOUNT,
            private_key=settings.EE_PRIVATE_KEY,
        )
        ee.Initialize(credentials, quiet=True)
    else:
        ee.Initialize()


def median_sample(
    collection_id: str,
    point: ee.Geometry,
    date_start: str,
    date_end: str,
    select_bands: list[str] | None = None,
    scale: int = 10,
) -> Dict[str, Any]:
    """Return a dict of median band values for the given point."""
    coll = (
        ee.ImageCollection(collection_id)
        .filterBounds(point)
        .filterDate(date_start, date_end)
    )
    if select_bands:
        coll = coll.select(select_bands)
    img = coll.median()
    feat = img.sample(region=point, scale=scale, geometries=False).first()
    return ee.Dictionary(feat).getInfo() if feat else {}

def median_sample(collection_id: str, point: ee.Geometry,
                  date_start: str, date_end: str,
                  scale: int = 10,
                  want_indices: bool = True) -> Dict[str, Any]:
    """Renvoie un dict des bandes + indices (NDVI, NDWI) médianes."""
    img = (ee.ImageCollection(collection_id)
           .filterBounds(point)
           .filterDate(date_start, date_end)
           .median())

    # ✔️ Ajouter NDVI et NDWI si demandé
    if want_indices and collection_id.startswith("COPERNICUS/S2"):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
        img = img.addBands([ndvi, ndwi])

    # Sélection finale : toutes les bandes disponibles 
    feat = img.sample(region=point, scale=scale,
                      geometries=False).first()
    return ee.Dictionary(feat).getInfo() if feat else {}

# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Fetch Sentinel‑1/2/3 data for every SoilProfile and store in teledection_data JSONField."

    def add_arguments(self, parser):
        parser.add_argument("--start", default="2024-01-01", help="YYYY‑MM‑DD")
        parser.add_argument("--end", default=str(dt.date.today()), help="YYYY‑MM‑DD")
        parser.add_argument(
            "--sensor",
            choices=["S1", "S2", "S3", "all"],
            default="all",
        )
        parser.add_argument("--scale", type=int, default=10)
        parser.add_argument("--batch", type=int, default=200)

    # ---------------------------------------------------------------------
    def handle(self, *args, **opts):
        # init_ee()
        authenticate_earth_engine()
        start, end = opts["start"], opts["end"]
        sensor, scale, batch_size = opts["sensor"], opts["scale"], opts["batch"]

        qs = SoilProfile.objects.all().order_by("id")
        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"→ {total} profils à traiter"))

        buffer: list[SoilProfile] = []
        for idx, profile in enumerate(qs.iterator(), 1):
            lon, lat = profile.location.x, profile.location.y
            ee_point = ee.Geometry.Point([lon, lat])
            sentinel_dict: Dict[str, Any] = {}

            try:
                if sensor in ("S2", "all"):
                    #ands: [B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12, AOT, WVP, SCL, TCI_R, TCI_G, TCI_B, MSK_CLDPRB, MSK_SNWPRB, QA10, QA20, QA60]
                    # sentinel_dict["S2"] = median_sample(
                    #     "COPERNICUS/S2_SR",
                    #     ee_point,
                    #     start,
                    #     end,
                    #     ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDWI"],
                    #     scale=scale,
                    # )
                    sentinel_dict["S2"] = median_sample(
                            "COPERNICUS/S2_SR", ee_point, start, end, scale=scale
                        )
                if sensor in ("S1", "all"):
                    sentinel_dict["S1"] = median_sample(
                        "COPERNICUS/S1_GRD",
                        ee_point,
                        start,
                        end,
                        ["VV", "VH"],
                        scale=scale,
                    )
                if sensor in ("S3", "all"):
                    sentinel_dict["S3"] = median_sample(
                        "COPERNICUS/S3/OLCI",
                        ee_point,
                        start,
                        end,
                        scale=300,
                    )
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.WARNING(f"Profil {profile.profile_id} – EE error: {exc}"))
                continue

            # merge & save
            merged = profile.teledection_data or {}
            merged.update(sentinel_dict)
            profile.teledection_data = merged
            buffer.append(profile)

            if len(buffer) >= batch_size:
                with transaction.atomic():
                    SoilProfile.objects.bulk_update(buffer, ["teledection_data"])
                self.stdout.write(self.style.SUCCESS(f"✓ {idx}/{total} mis à jour"))
                buffer.clear()

        if buffer:
            with transaction.atomic():
                SoilProfile.objects.bulk_update(buffer, ["teledection_data"])
            self.stdout.write(self.style.SUCCESS("✓ Mise à jour finale"))

        self.stdout.write(self.style.SUCCESS("✔ Terminé"))
