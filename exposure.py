"""Infrastructure exposure analysis via OSM Overpass API with local fallback."""
from __future__ import annotations
import requests
import pandas as pd
import numpy as np
import streamlit as st
from risk_model import haversine_km

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def get_demo_facilities(center_lat: float, center_lon: float) -> pd.DataFrame:
    """Generate realistic fallback facilities if Overpass API fails."""
    np.random.seed(42)
    types = [
        ("District Headquarter Hospital", "Hospital"),
        ("Sub-Divisional Hospital", "Hospital"),
        ("Community Health Centre", "Hospital"),
        ("Primary Health Centre", "Hospital"),
        ("Multipurpose Cyclone Shelter 1", "Shelter"),
        ("Govt Higher Secondary School (Shelter)", "Shelter"),
        ("Community Centre & Shelter", "Shelter"),
        ("Main Grid Substation 132kV", "Power"),
        ("Town Power Distribution Substation", "Power"),
        ("Emergency Evacuation Hub", "Shelter"),
    ]
    records = []
    for idx, (name, ftype) in enumerate(types):
        dlat = np.random.uniform(-0.35, 0.35)
        dlon = np.random.uniform(-0.35, 0.35)
        records.append({
            "id": f"demo_{idx}",
            "name": f"{name}",
            "type": ftype,
            "lat": round(center_lat + dlat, 4),
            "lon": round(center_lon + dlon, 4),
        })
    return pd.DataFrame(records)


def get_demo_roads(center_lat: float, center_lon: float) -> list[dict]:
    """Generate fallback road polylines if Overpass API fails."""
    return [
        {
            "name": "NH-16 Coastal Highway",
            "coords": [
                [center_lat - 0.4, center_lon - 0.25],
                [center_lat - 0.1, center_lon - 0.05],
                [center_lat + 0.15, center_lon + 0.1],
                [center_lat + 0.4, center_lon + 0.3],
            ],
        },
        {
            "name": "State Highway 2 (Evacuation Corridor)",
            "coords": [
                [center_lat - 0.3, center_lon + 0.35],
                [center_lat - 0.05, center_lon + 0.1],
                [center_lat + 0.2, center_lon - 0.15],
                [center_lat + 0.35, center_lon - 0.35],
            ],
        },
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_infrastructure(min_lat: float, min_lon: float, max_lat: float, max_lon: float,
                         center_lat: float, center_lon: float) -> tuple[pd.DataFrame, list[dict]]:
    """Fetch hospitals, shelters, power substations, and main roads from OSM Overpass with fallback."""
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"hospital|clinic"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      way["amenity"~"hospital|clinic"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      node["amenity"~"shelter|school|community_centre"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      node["emergency"="assembly_point"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      node["power"="substation"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      way["power"="substation"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
      way["highway"~"primary|trunk"]({min_lat:.4f},{min_lon:.4f},{max_lat:.4f},{max_lon:.4f});
    );
    out center geom;
    """
    facilities = []
    roads = []

    for endpoint in OVERPASS_MIRRORS:
        try:
            res = requests.post(endpoint, data={"data": query}, timeout=12)
            if res.status_code == 200:
                data = res.json()
                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    amenity = tags.get("amenity", "")
                    power = tags.get("power", "")
                    emergency = tags.get("emergency", "")
                    highway = tags.get("highway", "")

                    if highway in ["primary", "trunk"]:
                        name = tags.get("name", f"{highway.title()} Road")
                        geom = el.get("geometry", [])
                        if geom:
                            coords = [[pt["lat"], pt["lon"]] for pt in geom]
                            roads.append({"name": name, "coords": coords})
                    else:
                        ftype = "Other"
                        if amenity in ["hospital", "clinic"]:
                            ftype = "Hospital"
                        elif amenity in ["shelter", "school", "community_centre"] or emergency == "assembly_point":
                            ftype = "Shelter"
                        elif power == "substation":
                            ftype = "Power"

                        if ftype != "Other":
                            lat = el.get("lat") or el.get("center", {}).get("lat")
                            lon = el.get("lon") or el.get("center", {}).get("lon")
                            if lat and lon:
                                name = tags.get("name", f"Unnamed {ftype}")
                                facilities.append({
                                    "id": str(el.get("id")),
                                    "name": name,
                                    "type": ftype,
                                    "lat": round(lat, 4),
                                    "lon": round(lon, 4),
                                })
                if facilities or roads:
                    df_fac = pd.DataFrame(facilities) if facilities else get_demo_facilities(center_lat, center_lon)
                    return df_fac, roads if roads else get_demo_roads(center_lat, center_lon)
        except Exception:
            continue

    # Fallback to realistic demo data if API call times out or fails
    return get_demo_facilities(center_lat, center_lon), get_demo_roads(center_lat, center_lon)


def join_facilities_to_risk(facilities: pd.DataFrame, risk_grid: pd.DataFrame) -> pd.DataFrame:
    """Spatial join: Assign each facility to nearest risk grid cell and its risk band."""
    if facilities.empty:
        return facilities

    fac = facilities.copy()
    risk_lats = risk_grid["lat"].values
    risk_lons = risk_grid["lon"].values
    bands = risk_grid["band"].values
    floods = risk_grid["flood_m"].values
    scores = risk_grid["score"].values

    facility_bands = []
    facility_floods = []
    facility_scores = []

    for _, row in fac.iterrows():
        dists = haversine_km(row["lat"], row["lon"], risk_lats, risk_lons)
        nearest_idx = np.argmin(dists)
        facility_bands.append(bands[nearest_idx])
        facility_floods.append(round(float(floods[nearest_idx]), 1))
        facility_scores.append(round(float(scores[nearest_idx]), 3))

    fac["band"] = facility_bands
    fac["flood_m"] = facility_floods
    fac["risk_score"] = facility_scores
    return fac
