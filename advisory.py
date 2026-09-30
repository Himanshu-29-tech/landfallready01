"""Gemini-powered Early Warning Advisory generator with exponential backoff & rule fallback."""
from __future__ import annotations
import json
import time
import pandas as pd
import streamlit as st
from google import genai
from google.genai import errors, types
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACKS

SUPPORTED_LANGUAGES = ["English", "Hindi", "Bengali", "Odia", "Telugu"]


def build_context_dict(region_name: str, land_lat: float, land_lon: float, vmax: float,
                       rain_mm: float, weather_summary: dict, land_cells: int,
                       high_risk_cells: int, med_risk_cells: int, peak_flood_m: float,
                       facilities: pd.DataFrame) -> dict:
    """Build a compact, structured JSON context for LLM reasoning."""
    top_facs = []
    if not facilities.empty:
        top_exposed = facilities.sort_values(by=["risk_score", "flood_m"], ascending=False).head(8)
        for _, f in top_exposed.iterrows():
            top_facs.append({
                "name": f["name"],
                "type": f["type"],
                "risk_band": f["band"],
                "flood_depth_m": f["flood_m"],
            })

    return {
        "region": region_name,
        "landfall_target": {"lat": round(land_lat, 3), "lon": round(land_lon, 3)},
        "scenario": {
            "max_sustained_wind_kmh": vmax,
            "rain_72h_mm": rain_mm,
        },
        "live_weather_baseline": weather_summary,
        "impact_kpis": {
            "total_land_cells_analysed": land_cells,
            "high_risk_cells": high_risk_cells,
            "medium_risk_cells": med_risk_cells,
            "peak_flood_depth_m": peak_flood_m,
        },
        "exposed_facilities_sample": top_facs,
    }


def generate_rule_based_fallback(context: dict, language: str) -> dict:
    """Heuristic rule-based fallback advisory if Gemini API is unreachable."""
    region = context.get("region", "Coastal Area")
    kpis = context.get("impact_kpis", {})
    peak_flood = kpis.get("peak_flood_depth_m", 2.0)
    vmax = context.get("scenario", {}).get("max_sustained_wind_kmh", 160)
    high_cells = kpis.get("high_risk_cells", 0)

    return {
        "evacuate_zones": [
            f"Mandatory 100% evacuation for low-lying coastal sectors in {region} where surge flood depth exceeds {peak_flood}m.",
            f"Evacuate all temporary/kutcha structures within 20km radius of landfall target ({high_cells} high-risk sectors identified)."
        ],
        "priority_shelters": [
            "Activate all designated Multipurpose Cyclone Shelters at high elevation immediately.",
            "Preposition emergency food rations, drinking water purifiers, and backup generator fuel at shelters."
        ],
        "roads_likely_cut": [
            "Primary coastal trunk highways crossing low-lying creeks and estuaries.",
            "Secondary access roads within 10 km of the landfall target."
        ],
        "power_risk": f"Extreme power grid collapse risk due to {vmax} km/h sustained winds. Preventive power grid shutdown expected prior to eyewall arrival.",
        "medical_actions": [
            "Preposition trauma care units and snakebite anti-venom kits at inland sub-divisional hospitals.",
            "Ensure emergency backup generators at primary health centres have 72-hour fuel reserves."
        ],
        "time_windows": "Complete all mandatory evacuations at least T-12 hours before eyewall landfall.",
        "confidence_and_limitations": "RULE-BASED FALLBACK ADVISORY (Physics heuristic fallback used because live LLM model was unavailable or busy)."
    }


def call_gemini_advisory(context: dict, language: str, image_bytes: bytes | None = None,
                         image_mime: str = "image/jpeg") -> tuple[dict, str]:
    """Call Gemini API with retry logic (exponential backoff on 503) and fallback models. Returns (json_dict, model_used)."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=GEMINI_API_KEY)
    models_to_try = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]

    prompt = f"""
    DISASTER RESPONSE CONTEXT (JSON):
    {json.dumps(context, indent=2)}

    TASK:
    Generate an actionable early-warning advisory for municipal and disaster management authorities in {language} language.

    REQUIREMENTS:
    Return ONLY a valid JSON object matching this exact structure:
    {{
      "evacuate_zones": ["zone 1 description", "zone 2 description"],
      "priority_shelters": ["shelter action 1", "shelter action 2"],
      "roads_likely_cut": ["road segment 1", "road segment 2"],
      "power_risk": "detailed power grid risk assessment",
      "medical_actions": ["medical action 1", "medical action 2"],
      "time_windows": "critical evacuation and response time windows",
      "confidence_and_limitations": "confidence level and model limitations"
    }}

    IMPORTANT: Translate and write ALL string values inside the JSON object in {language}.
    Do NOT wrap in markdown codeblocks if possible, return clean valid JSON.
    """

    contents = []
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    contents.append(prompt)

    sys_instruction = (
        "You are a senior disaster-management specialist and meteorological risk analyst for coastal Asia. "
        "Provide precise, life-saving pre-landfall advisories for local governance and emergency services."
    )

    for model in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruction,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

                parsed = json.loads(text)
                return parsed, model
            except errors.ServerError:
                wait = 2 ** attempt
                time.sleep(wait)
            except errors.ClientError:
                break
            except Exception:
                time.sleep(1)

    raise RuntimeError("All Gemini API models failed")


@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_advisory(context_str: str, language: str, image_bytes: bytes | None = None) -> tuple[dict, str]:
    """Cached wrapper around Gemini call with fallback."""
    context = json.loads(context_str)
    try:
        parsed, model_used = call_gemini_advisory(context, language, image_bytes)
        return parsed, f"Gemini ({model_used})"
    except Exception:
        fallback = generate_rule_based_fallback(context, language)
        return fallback, "Rule-Based Heuristic Fallback"


def format_advisory_markdown(advisory: dict, region: str, language: str, source: str) -> str:
    """Format structured advisory JSON into clean markdown text for display and download."""
    evac = "\n".join(f"- {x}" for x in advisory.get("evacuate_zones", []))
    shelter = "\n".join(f"- {x}" for x in advisory.get("priority_shelters", []))
    roads = "\n".join(f"- {x}" for x in advisory.get("roads_likely_cut", []))
    medical = "\n".join(f"- {x}" for x in advisory.get("medical_actions", []))

    return f"""# 🌀 MUNICIPAL EARLY-WARNING DISASTER ADVISORY
**Target Region:** {region}  
**Language:** {language} | **Source:** {source}  

---

### 🚨 Mandatory Evacuation Zones
{evac}

### 🏫 Priority Shelter Activation & Emergency Logistics
{shelter}

### 🛣️ Transport Corridors & Road Submersion Risk
{roads}

### ⚡ Power Grid & Infrastructure Vulnerability
{advisory.get("power_risk", "High risk of power disruption.")}

### 🏥 Medical & Emergency Healthcare Actions
{medical}

### ⏱️ Critical Response Time Window
{advisory.get("time_windows", "Immediate action required.")}

---
> ℹ️ **Model Limitations & Confidence:** {advisory.get("confidence_and_limitations", "N/A")}
"""
