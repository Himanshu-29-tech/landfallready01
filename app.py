import time
import json
import folium
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_folium import st_folium

from config import REGIONS, GRID_STEPS
from data_sources import fetch_weather, summarize_weather, fetch_elevation
from risk_model import build_grid, compute_risk, haversine_km
from exposure import fetch_infrastructure, join_facilities_to_risk
from advisory import (
    SUPPORTED_LANGUAGES,
    build_context_dict,
    get_cached_advisory,
    format_advisory_markdown,
)
from insurance import evaluate_parametric_trigger
from home import render_home
from guide import render_guide, speak_custom_sentence
from guide_content import format_map_click_sentence

COLORS = {"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"}
MARKER_COLORS = {"High": "red", "Medium": "orange", "Low": "green", "Sea": "gray"}
ICONS = {"Hospital": "plus-sign", "Shelter": "home", "Power": "flash"}

st.set_page_config(page_title="LandfallReady - Cyclone Risk Forecaster", page_icon="🌀", layout="wide")

# Custom Dark Theme & Global Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f1f2f6;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #a4b0be;
        margin-bottom: 20px;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initializations
st.session_state.setdefault("guide_on", False)
st.session_state.setdefault("lang", "English")
st.session_state.setdefault("selected_region", list(REGIONS)[0])

st.markdown('<div class="main-title">🌀 LandfallReady</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Pre-Landfall Cyclone Risk & Infrastructure Exposure Forecaster | Bay of Bengal Coastal Action</div>', unsafe_allow_html=True)

# ---------- Sidebar: region, scenario, insurance, audio guide controls ----------
st.sidebar.header("📍 Region & Language")

current_reg = st.session_state["selected_region"]
reg_idx = list(REGIONS).index(current_reg) if current_reg in REGIONS else 0

region_name = st.sidebar.selectbox("Coastal Region", list(REGIONS), index=reg_idx, key="sb_region_choice")
st.session_state["selected_region"] = region_name
region = REGIONS[region_name]

# Language Selection synchronized with Home Page state
target_lang = st.sidebar.selectbox(
    "Advisory & Guide Language",
    SUPPORTED_LANGUAGES,
    index=SUPPORTED_LANGUAGES.index(st.session_state.get("lang", "English")),
)
st.session_state["lang"] = target_lang

st.sidebar.header("🔊 Audio Guidance")
guide_toggle = st.sidebar.checkbox("Enable Audio Guide", value=st.session_state["guide_on"])
st.session_state["guide_on"] = guide_toggle

st.sidebar.header("🌀 Cyclone Scenario")
vmax = st.sidebar.slider("Max sustained wind (km/h)", 60, 260, 160, 10)
rain_mm = st.sidebar.slider("72h accumulated rain (mm)", 0, 500, 250, 25)
off_lat = st.sidebar.slider("Landfall shift N/S (deg)", -0.5, 0.5, 0.0, 0.05)
off_lon = st.sidebar.slider("Landfall shift E/W (deg)", -0.5, 0.5, 0.0, 0.05)
land_lat, land_lon = region["lat"] + off_lat, region["lon"] + off_lon

st.sidebar.header("💳 Parametric Insurance Triggers")
wind_trigger = st.sidebar.slider("Wind Trigger (km/h)", 100, 220, 140, 5)
rain_trigger = st.sidebar.slider("Rain Trigger (mm)", 100, 400, 200, 10)
sum_insured = st.sidebar.number_input("Base Sum Insured per HH (₹)", 10000, 200000, 50000, 5000)

# ---------- Compute Core Models ----------
weather = fetch_weather(region["lat"], region["lon"])
summary = summarize_weather(weather)

grid, hl, ho = build_grid(region["lat"], region["lon"], region["radius_km"], GRID_STEPS)
elev = fetch_elevation(tuple(grid["lat"]), tuple(grid["lon"]))
if elev is None:
    st.warning("⚠️ Elevation API unavailable, using flat 5m elevation fallback (demo mode).")
    elev = [5.0] * len(grid)

risk = compute_risk(grid, elev, land_lat, land_lon, vmax, rain_mm)
land = risk[risk["is_land"]]

min_lat, max_lat = grid["lat"].min(), grid["lat"].max()
min_lon, max_lon = grid["lon"].min(), grid["lon"].max()
raw_fac, roads = fetch_infrastructure(min_lat, min_lon, max_lat, max_lon, region["lat"], region["lon"])
facilities = join_facilities_to_risk(raw_fac, risk)

high_risk_cells = risk[risk["band"] == "High"]
high_lats = high_risk_cells["lat"].values
high_lons = high_risk_cells["lon"].values

# Parametric Insurance Evaluation
ins_eval = evaluate_parametric_trigger(
    max_wind=vmax,
    rain_72h=rain_mm,
    wind_threshold=wind_trigger,
    rain_threshold=rain_trigger,
    base_sum_insured_inr=sum_insured,
)

# ---------- Tabbed Navigation ----------
tab_home, tab_overview, tab_map, tab_infra, tab_advisory, tab_insurance = st.tabs([
    "🏠 Home",
    "📊 Overview & Baseline",
    "🗺️ Cyclone Risk Map",
    "🏥 Infrastructure Exposure",
    "🤖 Gemini AI Advisory",
    "💳 Parametric Insurance",
])

# ==================== TAB 0: HOME ====================
with tab_home:
    render_home(region_name, vmax, rain_mm, risk, weather)

# ==================== TAB 1: OVERVIEW ====================
with tab_overview:
    st.subheader(f"Impact Summary for {region_name}")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Land Cells Analysed", len(land))
    k2.metric("🔴 High Risk Cells", int((land["band"] == "High").sum()))
    k3.metric("🟠 Medium Risk Cells", int((land["band"] == "Medium").sum()))
    k4.metric("Peak Flood Depth (m)", round(float(land["flood_m"].max()), 1))

    st.markdown("---")
    with st.expander("🌐 Live Meteorological Forecast Baseline (Open-Meteo, Next 72h)", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Live Max Wind (km/h)", summary["max_wind"])
        c2.metric("Live Max Gust (km/h)", summary["max_gust"])
        c3.metric("Live 72h Rain (mm)", summary["rain_72h"])
        c4.metric("Live Min Pressure (hPa)", summary["min_pressure"])
        if "error" not in weather:
            df_w = pd.DataFrame({"wind": weather["wind"], "gust": weather["gust"]},
                                index=pd.to_datetime(weather["time"]))
            st.line_chart(df_w)

    st.markdown("---")
    st.markdown("### 💡 How LandfallReady Works & System Architecture")
    st.markdown("""
    - **Shift from Post-Landfall Recovery to Pre-Landfall Action:** LandfallReady processes real-time meteorological forecasts and elevation topography to compute pre-landfall storm surge depth, exponential wind decay, and rainfall flood susceptibility.
    - **Heuristic Physical Model:** Risk per cell is a weighted index: $0.5 \\cdot \\text{flood depth} + 0.3 \\cdot \\text{wind ratio} + 0.2 \\cdot \\text{rain susceptibility}$.
    - **Multimodal AI Reasoning:** Gemini 3.7 Flash parses spatial risk parameters alongside satellite imagery to generate structured municipal advisories in regional Indian languages.
    - **BRICS & APAC Federated Sharing Concept:** Designed to allow cross-border coastal nations (India, Bangladesh, Myanmar, Sri Lanka) to securely federate cyclone risk parameters without exposing private infrastructure topology.
    """)

# ==================== TAB 2: RISK MAP ====================
with tab_map:
    st.subheader(f"Spatial Risk Map - {region_name}")
    st.caption("Click any location on the map to inspect elevation, flood depth, wind speed, and distance to nearest hospital.")

    m = folium.Map(location=[region["lat"], region["lon"]], zoom_start=8, tiles="OpenStreetMap")
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite (Esri)",
    ).add_to(m)

    fg_grid = folium.FeatureGroup(name="Risk Grid", show=True)
    for r in land.itertuples():
        folium.Rectangle(
            bounds=[[r.lat - hl, r.lon - ho], [r.lat + hl, r.lon + ho]],
            stroke=False, fill=True, fill_color=COLORS[r.band], fill_opacity=0.45,
            tooltip=f"{r.band} | elev {r.elev:.0f} m | surge {r.surge_m:.1f} m | flood {r.flood_m:.1f} m | wind {r.wind:.0f} km/h",
        ).add_to(fg_grid)
    fg_grid.add_to(m)

    fg_hosp = folium.FeatureGroup(name="Hospitals", show=True)
    fg_shelt = folium.FeatureGroup(name="Shelters", show=True)
    fg_power = folium.FeatureGroup(name="Power Substations", show=True)

    for f in facilities.itertuples():
        m_color = MARKER_COLORS.get(f.band, "blue")
        icon_name = ICONS.get(f.type, "info-sign")
        marker = folium.Marker(
            location=[f.lat, f.lon],
            tooltip=f"{f.name} ({f.type}) - Risk: {f.band} | Flood: {f.flood_m} m",
            icon=folium.Icon(color=m_color, icon=icon_name)
        )
        if f.type == "Hospital":
            marker.add_to(fg_hosp)
        elif f.type == "Shelter":
            marker.add_to(fg_shelt)
        elif f.type == "Power":
            marker.add_to(fg_power)

    fg_hosp.add_to(m)
    fg_shelt.add_to(m)
    fg_power.add_to(m)

    fg_roads = folium.FeatureGroup(name="Primary Roads", show=True)
    for r in roads:
        coords = r.get("coords", [])
        if len(coords) < 2:
            continue
        crosses_high = False
        if len(high_lats) > 0:
            for r_lat, r_lon in coords:
                dists = haversine_km(r_lat, r_lon, high_lats, high_lons)
                if (dists < 5.0).any():
                    crosses_high = True
                    break
        line_color = "#d63031" if crosses_high else "#0984e3"
        line_weight = 5 if crosses_high else 3
        popup_text = f"HIGH RISK CUTOFF LIKELY: {r['name']}" if crosses_high else r['name']
        folium.PolyLine(
            locations=coords,
            color=line_color,
            weight=line_weight,
            opacity=0.8,
            tooltip=popup_text,
        ).add_to(fg_roads)
    fg_roads.add_to(m)

    folium.Marker([land_lat, land_lon], tooltip="Projected Landfall Eye Target",
                  icon=folium.Icon(color="darkred", icon="warning-sign")).add_to(m)

    folium.LayerControl().add_to(m)
    st_map = st_folium(m, height=540, use_container_width=True)

    # ---------- Phase C: Map Click Inspection & Audio Speech ----------
    last_clicked = st_map.get("last_clicked")
    if last_clicked:
        c_lat, c_lon = last_clicked["lat"], last_clicked["lng"]

        # Spatial lookup for nearest risk cell
        dists = haversine_km(c_lat, c_lon, risk["lat"].values, risk["lon"].values)
        n_idx = np.argmin(dists)
        cell = risk.iloc[n_idx]

        # Distance to nearest hospital
        hosps = facilities[facilities["type"] == "Hospital"]
        if not hosps.empty:
            h_dists = haversine_km(c_lat, c_lon, hosps["lat"].values, hosps["lon"].values)
            min_hosp_dist = float(np.min(h_dists))
        else:
            min_hosp_dist = 12.5

        click_speech = format_map_click_sentence(
            language=st.session_state["lang"],
            lat=c_lat,
            lon=c_lon,
            band=str(cell["band"]),
            elev=float(cell["elev"]),
            flood_m=float(cell["flood_m"]),
            wind=float(cell["wind"]),
            dist_hosp=min_hosp_dist,
        )

        st.markdown("---")
        st.info(f"📍 **Inspected Map Location:** Lat `{c_lat:.3f}`, Lon `{c_lon:.3f}` | **Risk Band:** `{cell['band']}` | **Flood Depth:** `{cell['flood_m']:.1f} m` | **Wind:** `{cell['wind']:.0f} km/h` | **Nearest Hospital:** `{min_hosp_dist:.1f} km`")

        # Speak via audio guide if enabled and new click
        if st.session_state.get("guide_on"):
            last_click_str = f"{c_lat:.4f}_{c_lon:.4f}"
            if last_click_str != st.session_state.get("last_click_nonce"):
                st.session_state["last_click_nonce"] = last_click_str
                nonce_str = f"{last_click_str}_{time.time()}"
                speak_custom_sentence(click_speech, st.session_state["lang"], nonce_str)

# ==================== TAB 3: INFRASTRUCTURE ====================
with tab_infra:
    st.subheader("🏥 Critical Infrastructure Exposure Breakdown")
    if not facilities.empty:
        hosp_high = len(facilities[(facilities["type"] == "Hospital") & (facilities["band"] == "High")])
        shelt_high = len(facilities[(facilities["type"] == "Shelter") & (facilities["band"] == "High")])
        power_high = len(facilities[(facilities["type"] == "Power") & (facilities["band"] == "High")])

        i1, i2, i3 = st.columns(3)
        i1.metric("🏥 Hospitals in High Risk Zone", hosp_high)
        i2.metric("🏫 Shelters in High Risk Zone", shelt_high)
        i3.metric("⚡ Power Substations in High Risk Zone", power_high)

        st.markdown("---")
        st.subheader("📋 Exposed Facilities Detail Table")
        display_df = facilities[["name", "type", "band", "flood_m", "risk_score", "lat", "lon"]].sort_values(
            by=["risk_score", "flood_m"], ascending=False
        )
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No infrastructure facilities found for this region bounding box.")

# ==================== TAB 4: GEMINI ADVISORY ====================
with tab_advisory:
    st.subheader("🤖 Gemini Multimodal Early-Warning Advisory Engine")
    st.caption("Generates structured emergency advisories for municipal authorities in regional Indian languages.")

    col_upload, col_action = st.columns([1, 1])
    with col_upload:
        uploaded_img = st.file_uploader(
            "Upload Satellite / Radar / Cloud Imagery (Optional Multimodal Analysis)",
            type=["jpg", "jpeg", "png"],
        )
        img_bytes = None
        if uploaded_img:
            img_bytes = uploaded_img.read()
            st.image(img_bytes, caption="Uploaded Satellite Imagery Context", use_container_width=True)

    with col_action:
        st.write("**Advisory Generation Options**")
        st.write(f"Target Language: `{target_lang}`")
        st.write(f"Selected Region: `{region_name}`")
        st.write(f"Scenario Wind / Rain: `{vmax} km/h` | `{rain_mm} mm`")
        gen_btn = st.button("🌀 Generate Municipal Advisory", use_container_width=True)

    if gen_btn:
        ctx_dict = build_context_dict(
            region_name=region_name,
            land_lat=land_lat,
            land_lon=land_lon,
            vmax=vmax,
            rain_mm=rain_mm,
            weather_summary=summary,
            land_cells=len(land),
            high_risk_cells=int((land["band"] == "High").sum()),
            med_risk_cells=int((land["band"] == "Medium").sum()),
            peak_flood_m=round(float(land["flood_m"].max()), 1),
            facilities=facilities,
        )
        ctx_str = json.dumps(ctx_dict, sort_keys=True)

        with st.spinner("Calling Gemini AI Engine (with exponential backoff & auto fallback)..."):
            adv_json, source = get_cached_advisory(ctx_str, target_lang, img_bytes)
            adv_md = format_advisory_markdown(adv_json, region_name, target_lang, source)
            st.session_state["advisory_md"] = adv_md
            st.session_state["advisory_source"] = source

    if "advisory_md" in st.session_state:
        st.success(f"Advisory generated via {st.session_state.get('advisory_source')}")
        st.markdown(st.session_state["advisory_md"])
        st.download_button(
            label="📥 Download Advisory as Markdown File",
            data=st.session_state["advisory_md"],
            file_name=f"landfall_advisory_{region_name.split()[0].lower()}_{target_lang.lower()}.md",
            mime="text/markdown",
        )

# ==================== TAB 5: INSURANCE ====================
with tab_insurance:
    st.subheader("💳 Pre-Landfall Parametric Insurance Trigger Card")
    st.caption("Automated liquidity trigger based on objective meteorological parameter thresholds (Illustrative Model).")

    p1, p2, p3 = st.columns(3)
    p1.metric("Scenario Max Wind", f"{vmax} km/h", delta=f"{vmax - wind_trigger} vs trigger")
    p2.metric("Scenario 72h Rain", f"{rain_mm} mm", delta=f"{rain_mm - rain_trigger} vs trigger")
    p3.metric("Evaluated Trigger Tier", ins_eval["tier_name"].split(" ")[1])

    st.markdown(f"""
    <div style="background-color: #1e272e; border-left: 6px solid {ins_eval['status_color']}; padding: 20px; border-radius: 8px; margin-top: 15px;">
        <h3 style="color: {ins_eval['status_color']}; margin-top:0px;">{ins_eval['tier_name']}</h3>
        <p style="font-size: 1.1rem;"><strong>Evaluation Summary:</strong> {ins_eval['description']}</p>
        <hr style="border-color: rgba(255,255,255,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4>Payout Ratio: <span style="color: {ins_eval['status_color']};">{ins_eval['payout_pct']}%</span></h4>
                <p>Base Sum Insured per Household: <strong>₹{sum_insured:,.2f}</strong></p>
            </div>
            <div style="text-align: right; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px;">
                <p style="margin:0; font-size: 0.9rem; color: #a4b0be;">Illustrative Payout per Household</p>
                <h2 style="margin:0; color: #2ecc71;">₹{ins_eval['payout_per_hh_inr']:,.2f}</h2>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📜 Parametric Policy Rules & Trigger Logic")
    st.markdown("""
    - **Tier 0 (0% Payout):** Neither wind speed nor 72h accumulated rain breaches policy trigger thresholds.
    - **Tier 1 (25% Payout):** Single parameter breach (either Wind $\\ge$ Trigger OR Rain $\\ge$ Trigger). Unlocks immediate early liquidity for emergency food and evacuation transport.
    - **Tier 2 (50% Payout):** Compound breach (both Wind $\\ge$ Trigger AND Rain $\\ge$ Trigger). Unlocks immediate liquidity for temporary shelter and crop loss buffer.
    - **Tier 3 (100% Payout):** Catastrophic breach (both Wind AND Rain exceed 125% of trigger thresholds). Maximum payout disbursed automatically prior to landfall.
    - *Disclaimer: This card is an illustrative proof-of-concept for pre-disaster parametric micro-insurance financing.*
    """)

# ---------- Render Floating Audio Guide Widget ----------
render_guide(st.session_state["lang"], st.session_state["guide_on"])
