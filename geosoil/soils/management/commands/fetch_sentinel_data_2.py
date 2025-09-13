# -*- coding: utf-8 -*-
"""fetch_sentinel_data.py – v2  (homogeneous Sentinel‑2 """

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import ee
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from soils.models import SoilProfile

# ---------------------------------------------------------------------------
# EE init -------------------------------------------------------------------
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


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


# ---------------------------------------------------------------------------
# Helpers -------------------------------------------------------------------

S2_BANDS: List[str] = [
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B8A",
    "B9",
    "B11",
    "B12",
    "AOT",
    "WVP",
]


def s2_prepare(img: ee.Image) -> ee.Image:
    """Select a stable subset of bands then add NDVI/NDWI."""
    img = img.select(S2_BANDS)
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
    return img.addBands([ndvi, ndwi])


def median_sample(
    point: ee.Geometry,
    date_start: str,
    date_end: str,
    sensor: str,
    scale: int = 10,
) -> Dict[str, Any]:
    """Return median dict for the requested sensor (S1/S2/S3)."""

    if sensor == "S2":
        coll = (
            ee.ImageCollection("COPERNICUS/S2_SR")
            .filterBounds(point)
            .filterDate(date_start, date_end)
            .map(s2_prepare)
        )
    elif sensor == "S1":
        coll = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(point)
            .filterDate(date_start, date_end)
            .select(["VV", "VH"])
        )
    elif sensor == "S3":
        coll = (
            ee.ImageCollection("COPERNICUS/S3/OLCI")
            .filterBounds(point)
            .filterDate(date_start, date_end)
        )
    else:
        raise ValueError("Unknown sensor")

    img = coll.median()
    feat = img.sample(region=point, scale=scale, geometries=False).first()
    return ee.Dictionary(feat).getInfo() if feat else {}


# ---------------------------------------------------------------------------
# Management command --------------------------------------------------------

class Command(BaseCommand):
    help = "Attach Sentinel median values to SoilProfile.teledection_data (JSON)."

    def add_arguments(self, parser):
        parser.add_argument("--start", default="2024-01-01")
        parser.add_argument("--end", default=str(dt.date.today()))
        parser.add_argument("--sensor", choices=["S1", "S2", "S3", "all"], default="all")
        parser.add_argument("--scale", type=int, default=10)
        parser.add_argument("--batch", type=int, default=200)

    def handle(self, *args, **opts):
        authenticate_earth_engine()
        start, end = opts["start"], opts["end"]
        sensor_choice, scale, batch_size = opts["sensor"], opts["scale"], opts["batch"]

        qs = SoilProfile.objects.all().order_by("id")
        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"→ {total} profils à traiter"))

        buffer: List[SoilProfile] = []
        for profile in tqdm(qs.iterator(), total=total, unit="profil", colour="green"):
            ee_point = ee.Geometry.Point([profile.location.x, profile.location.y])
            sentinel_dict: Dict[str, Any] = {}

            try:
                if sensor_choice in ("S2", "all"):
                    sentinel_dict["S2"] = median_sample(
                        ee_point, start, end, "S2", scale=scale
                    )
                if sensor_choice in ("S1", "all"):
                    sentinel_dict["S1"] = median_sample(
                        ee_point, start, end, "S1", scale=scale
                    )
                if sensor_choice in ("S3", "all"):
                    sentinel_dict["S3"] = median_sample(
                        ee_point, start, end, "S3", scale=300
                    )
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.WARNING(f"Profil {profile.profile_id}: {exc}"))
                continue

            merged = profile.teledection_data or {}
            merged.update({k: v for k, v in sentinel_dict.items() if v})
            profile.teledection_data = merged
            buffer.append(profile)

            if len(buffer) >= batch_size:
                with transaction.atomic():
                    SoilProfile.objects.bulk_update(buffer, ["teledection_data"])
                buffer.clear()

        if buffer:
            with transaction.atomic():
                SoilProfile.objects.bulk_update(buffer, ["teledection_data"])

        self.stdout.write(self.style.SUCCESS("✔ Terminé"))
