"""Heuristic cyclone risk model (NOT a hydrodynamic simulation).

Risk per grid cell = weighted blend of:
  - storm-surge flood depth (surge height minus ground elevation)
  - wind intensity at that cell (decays with distance from landfall)
  - rainfall flood susceptibility (heavier impact on low-lying land)
"""
from __future__ import annotations
import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Works on numpy arrays."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def build_grid(lat: float, lon: float, radius_km: float, steps: int):
    """Square lat/lon grid around a centre point. Returns (df, half_dlat, half_dlon)."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * np.cos(np.radians(lat)))
    lats = np.linspace(lat - dlat, lat + dlat, steps)
    lons = np.linspace(lon - dlon, lon + dlon, steps)
    la, lo = np.meshgrid(lats, lons, indexing="ij")
    df = pd.DataFrame({"lat": la.ravel(), "lon": lo.ravel()})
    return df, dlat / (steps - 1), dlon / (steps - 1)


def compute_risk(grid: pd.DataFrame, elevation, landfall_lat: float,
                 landfall_lon: float, vmax: float, rain_mm: float,
                 wind_scale_km: float = 120.0) -> pd.DataFrame:
    df = grid.copy()
    df["elev"] = np.asarray(elevation, dtype=float)
    df["is_land"] = df["elev"] > 0.5

    # 1) distance to landfall -> wind decays exponentially
    df["dist_km"] = haversine_km(df["lat"], df["lon"], landfall_lat, landfall_lon)
    df["wind"] = vmax * np.exp(-df["dist_km"] / wind_scale_km)

    # 2) surge height ~ wind^2 (200 km/h -> ~6 m), flood depth = surge - elevation
    df["surge_m"] = 6.0 * (df["wind"] / 200.0) ** 2
    df["flood_m"] = np.clip(df["surge_m"] - df["elev"], 0, None)

    # 3) rain susceptibility: low ground floods more
    susceptibility = np.where(df["elev"] < 10, 1.0, np.where(df["elev"] < 30, 0.5, 0.2))
    df["rain_risk"] = np.clip(rain_mm / 300.0, 0, 1) * susceptibility

    # 4) weighted score 0..1
    score = (0.5 * np.clip(df["flood_m"] / 3.0, 0, 1)
             + 0.3 * np.clip(df["wind"] / 180.0, 0, 1)
             + 0.2 * df["rain_risk"])
    df["score"] = score.round(3)
    df["band"] = np.where(~df["is_land"], "Sea",
                 np.where(score < 0.25, "Low",
                 np.where(score < 0.50, "Medium", "High")))
    return df
