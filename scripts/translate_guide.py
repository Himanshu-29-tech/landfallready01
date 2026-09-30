"""Script to translate English guide sentences to Bengali, Odia, and Telugu using Gemini API."""
import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.7-flash"))
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

GEMINI_FALLBACKS = ["gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-flash"]

ENGLISH_GUIDE = {
    "welcome": "Welcome to LandfallReady. I will guide you. Move your cursor or click on any part of the screen and I will explain it.",
    "sidebar_region": "Select your target coastal region along the Bay of Bengal to analyze cyclone impact.",
    "sidebar_wind": "Adjust maximum sustained wind speed to simulate cyclone intensity.",
    "sidebar_rain": "Adjust 72-hour accumulated rainfall to estimate flooding and ground saturation.",
    "sidebar_landfall_shift": "Shift projected landfall coordinates north, south, east, or west to test track uncertainty.",
    "kpi_strip": "These metrics show total land cells analyzed, high and medium risk counts, and peak flood depth.",
    "map_area": "Interactive risk map showing colored flood cells, projected landfall eye, and exposed infrastructure.",
    "map_click": "Click any grid cell or facility marker to inspect exact risk level, elevation, and flood depth.",
    "map_satellite_toggle": "Toggle top-right map controls to switch between street map and Esri satellite imagery.",
    "map_layers": "Use layer controls to toggle hospitals, shelters, power stations, and primary road networks.",
    "hospital_marker": "Hospital marker indicating flood risk level and emergency medical vulnerability.",
    "shelter_marker": "Designated cyclone shelter location mapped to surrounding flood depth and risk score.",
    "substation_marker": "Electrical power substation vulnerable to wind damage and power grid disruption.",
    "road_layer": "Primary highways and evacuation routes. Red segments highlight probable flood cutoffs.",
    "infra_table": "Detailed table listing all exposed critical facilities sorted by risk score and flood depth.",
    "advisory_generate": "Click here to generate an AI-powered municipal early-warning advisory in your chosen language.",
    "advisory_language": "Choose target regional language for official municipal disaster management advisories.",
    "advisory_upload": "Upload satellite or cloud imagery for multimodal storm structure analysis.",
    "advisory_download": "Download the complete municipal disaster advisory as a markdown text file.",
    "insurance_card": "Pre-landfall parametric insurance trigger evaluation showing household liquidity payout tier.",
    "insurance_thresholds": "Adjust wind and rain policy thresholds to test parametric payout conditions.",
    "tab_home": "Home page with quick start guided tour, overview cards, and application workflow.",
    "tab_overview": "High-level disaster metrics, live weather baseline, and system architecture breakdown.",
    "tab_map": "Full-screen interactive spatial risk map with satellite tiles and layer controls.",
    "tab_infra": "Critical infrastructure exposure breakdown for hospitals, shelters, and power substations.",
    "tab_advisory": "Gemini multimodal AI advisory generator for municipal decision makers.",
    "tab_insurance": "Parametric micro-insurance trigger card and household payout calculator.",
}


def translate_dict(target_lang: str) -> dict:
    if not GEMINI_API_KEY:
        print(f"Warning: GEMINI_API_KEY missing, using English fallback for {target_lang}")
        return ENGLISH_GUIDE

    client = genai.Client(api_key=GEMINI_API_KEY)
    models = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]

    prompt = f"""
    Translate the following JSON dictionary of user interface guide sentences into {target_lang}.
    Keep sentences short (max 20 words), clear, and natural for speech synthesis.
    Return ONLY a valid JSON dictionary with the exact same keys.

    INPUT JSON:
    {json.dumps(ENGLISH_GUIDE, indent=2)}
    """

    for model in models:
        for attempt in range(3):
            try:
                r = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                text = r.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                return json.loads(text.strip())
            except errors.ServerError:
                wait = 2 ** attempt
                time.sleep(wait)
            except Exception as e:
                print(f"Model {model} failed attempt {attempt}: {e}")
                break

    print(f"Error: All models failed for {target_lang}, using English fallback.")
    return ENGLISH_GUIDE


def main():
    translations = {}
    for lang in ["Bengali", "Odia", "Telugu"]:
        print(f"Translating guide content to {lang}...")
        translations[lang] = translate_dict(lang)

    out_path = os.path.join(os.path.dirname(__file__), "..", "guide_translations.json")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    print(f"Saved guide translations to {out_path}")


if __name__ == "__main__":
    main()
