"""Central configuration: presets, thresholds, constants."""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.7-flash"))
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

GEMINI_FALLBACKS = ["gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-flash"]

# Preset coastal regions: representative landfall point + analysis radius
REGIONS = {
    "Odisha (Puri coast)": {"lat": 19.80, "lon": 85.83, "radius_km": 120},
    "Andhra Pradesh (Visakhapatnam)": {"lat": 17.69, "lon": 83.22, "radius_km": 120},
    "West Bengal (Digha / Sundarbans)": {"lat": 21.63, "lon": 87.55, "radius_km": 120},
    "Bangladesh (Cox's Bazar)": {"lat": 21.43, "lon": 91.98, "radius_km": 120},
}

GRID_STEPS = 18
EARTH_RADIUS_KM = 6371.0
