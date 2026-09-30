"""External data fetchers with caching and graceful fallbacks."""
from __future__ import annotations
import requests
import streamlit as st

TIMEOUT = 15


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(lat: float, lon: float) -> dict:
    """72h hourly forecast from Open-Meteo (free, no key)."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_gusts_10m,precipitation,pressure_msl",
        "forecast_days": 3,
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        h = r.json()["hourly"]
        return {
            "time": h["time"],
            "wind": h["wind_speed_10m"],
            "gust": h["wind_gusts_10m"],
            "rain": h["precipitation"],
            "pressure": h["pressure_msl"],
            "source": "Open-Meteo live",
        }
    except Exception as e:
        return {"error": str(e), "source": "fallback"}


def summarize_weather(w: dict) -> dict:
    """Reduce hourly series to decision-ready numbers."""
    if "error" in w:
        return {"max_wind": 0, "max_gust": 0, "rain_72h": 0, "min_pressure": 0}
    return {
        "max_wind": max(x or 0 for x in w["wind"]),
        "max_gust": max(x or 0 for x in w["gust"]),
        "rain_72h": round(sum(x or 0 for x in w["rain"]), 1),
        "min_pressure": min(x for x in w["pressure"] if x),
    }


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_elevation(lats: tuple, lons: tuple) -> list | None:
    """Ground elevation (m) per point via Open-Meteo. Max 100 points/request."""
    out: list[float] = []
    try:
        for i in range(0, len(lats), 100):
            params = {
                "latitude": ",".join(f"{x:.4f}" for x in lats[i:i + 100]),
                "longitude": ",".join(f"{x:.4f}" for x in lons[i:i + 100]),
            }
            r = requests.get("https://api.open-meteo.com/v1/elevation",
                             params=params, timeout=TIMEOUT)
            r.raise_for_status()
            out.extend(r.json()["elevation"])
        return out
    except Exception:
        return None
