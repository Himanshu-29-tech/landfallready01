"""Redesigned Weather-Dashboard Home Page for LandfallReady."""
import html as html_lib
import base64
import os
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from config import REGIONS


def _bg_uri() -> str:
    for p in ["assets/cyclone.jpg", "assets/cyclone.webp", "assets/l56220260910181745_jpeg.webp"]:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                ext = p.split(".")[-1].lower()
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/webp"
                return f"data:{mime};base64,{b64}"
            except Exception:
                pass
    return ""


def get_risk_status(vmax: float, peak_flood: float, high_cell_pct: float):
    if vmax >= 180 or peak_flood >= 4.0 or high_cell_pct >= 40:
        return "Extreme", "#e74c3c"
    elif vmax >= 140 or peak_flood >= 2.5 or high_cell_pct >= 25:
        return "Dangerous", "#e67e22"
    elif vmax >= 100 or peak_flood >= 1.0 or high_cell_pct >= 10:
        return "Elevated", "#f1c40f"
    return "Low", "#2ecc71"


def get_headline(region: str, vmax: float, peak_flood: float, lang: str) -> str:
    clean = region.split("(")[0].strip()
    if lang == "Hindi":
        return f"Teevra cyclone {clean} tatiye kshetra ke samip.<br><strong>{peak_flood:.1f}m surge</strong> aur bhari varsha."
    elif lang == "Bengali":
        return f"{clean} উপকূলে তীব্র ঘূর্ণিঝড়।<br><strong>{peak_flood:.1f}মি জলচ্ছ্বাস</strong> ও ভারী বৃষ্টি।"
    elif lang == "Odia":
        return f"{clean} ଉପକୂଳ ଆଡ଼କୁ ଗମ୍ଭୀର ବାତ୍ୟା।<br><strong>{peak_flood:.1f}ମି ଜଳପ୍ଲାବନ</strong> ସମ୍ଭାବନା।"
    elif lang == "Telugu":
        return f"{clean} తీరానికి తీవ్ర తుఫాను।<br><strong>{peak_flood:.1f}మీ అలలు</strong> మరియు భారీ వర్షపాతం।"
    return f"Severe cyclone approaching <strong>{clean}</strong> coast.<br>Expecting <strong>{peak_flood:.1f}m surge</strong> &amp; extreme rainfall."


def _wave_html(winds: list) -> str:
    if not winds:
        return ""
    max_w = max(winds) or 1
    peak_idx = winds.index(max(winds))
    W, H = 700, 50
    step_x = W / max(len(winds) - 1, 1)
    pts, peak_x, peak_y = [], 0.0, 0.0
    for i, w in enumerate(winds):
        x = i * step_x
        y = H - (w / (max_w * 1.2)) * H
        pts.append(f"{x:.1f},{y:.1f}")
        if i == peak_idx:
            peak_x, peak_y = x, y
    path_d = "M " + " L ".join(pts)
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    days_row = "".join(
        f'<div style="flex:1;text-align:center;font-size:.78rem;color:rgba(255,255,255,.55);">{day_labels[i % 7]}</div>'
        for i in range(len(winds))
    )
    vals_row = "".join(
        f'<div style="flex:1;text-align:center;font-size:{"1.5rem" if i==peak_idx else "1.1rem"};'
        f'color:{"#fff;text-shadow:0 0 12px rgba(255,255,255,.8)" if i==peak_idx else "rgba(255,255,255,.4)"};'
        f'font-weight:{"400" if i==peak_idx else "300"};">{int(w)}</div>'
        for i, w in enumerate(winds)
    )
    return f"""
<div style="margin-top:22px;">
  <div style="display:flex;margin-bottom:5px;">{days_row}</div>
  <svg width="100%" height="55" viewBox="0 0 700 55" style="overflow:visible;">
    <defs>
      <filter id="wg">
        <feGaussianBlur stdDeviation="3" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <line x1="{peak_x:.1f}" y1="0" x2="{peak_x:.1f}" y2="55"
          stroke="rgba(255,255,255,.22)" stroke-dasharray="3,3"/>
    <path d="{path_d}" fill="none" stroke="#ffffff" stroke-width="2.5" filter="url(#wg)"/>
    <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="5" fill="#fff" filter="url(#wg)"/>
  </svg>
  <div style="display:flex;margin-top:5px;">{vals_row}</div>
</div>"""


def render_home(
    region_name: str = "Odisha (Puri coast)",
    vmax: float = 160.0,
    rain_mm: float = 250.0,
    risk_df: pd.DataFrame | None = None,
    weather: dict | None = None,
):
    """Render full-screen glassmorphic home dashboard."""
    if risk_df is not None and not risk_df.empty:
        land_df = risk_df[risk_df["is_land"]] if "is_land" in risk_df.columns else risk_df
        total = max(len(land_df), 1)
        high_cells = int((land_df["band"] == "High").sum())
        high_pct = round((high_cells / total) * 100, 1)
        peak_flood = float(land_df["flood_m"].max()) if not land_df.empty else 2.5
    else:
        high_pct = 23.8
        peak_flood = 4.2

    status_label, status_color = get_risk_status(vmax, peak_flood, high_pct)
    today_str = datetime.date.today().strftime("%A, %b %d")
    lang = st.session_state.get("lang", "English")
    headline = get_headline(region_name, vmax, peak_flood, lang)
    region_safe = html_lib.escape(region_name)

    if weather and "error" not in weather and weather.get("wind"):
        winds = [w or 0 for w in weather["wind"][:28:4]]
    else:
        winds = [60, 95, 140, vmax, 150, 110, 85]

    wave_html = _wave_html(winds)
    bg = _bg_uri()
    bg_css = (
        f"background: linear-gradient(180deg,rgba(10,14,22,.52) 0%,rgba(10,14,22,.90) 100%),"
        f"url('{bg}') center/cover no-repeat fixed;"
        if bg else
        "background: linear-gradient(135deg,#0d1117 0%,#161b27 60%,#0a0e16 100%);"
    )

    quick_btns = "".join(
        f'<div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.11);'
        f'border-radius:14px;padding:10px 14px;margin-bottom:10px;font-size:.85rem;color:#dfe6e9;">'
        f'🌀 {html_lib.escape(r.split("(")[0].strip())}</div>'
        for r in list(REGIONS) if r != region_name
    )[:3]

    hero_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',sans-serif;color:#f1f2f6;overflow-x:hidden;background:transparent;}}
.hero{{{bg_css}border-radius:26px;border:1px solid rgba(255,255,255,.10);padding:26px 30px;box-shadow:0 24px 60px rgba(0,0,0,.7);}}
.grid{{display:grid;grid-template-columns:230px 1fr 190px;gap:18px;align-items:start;}}
.left{{background:rgba(16,22,36,.62);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:20px;border:1px solid rgba(255,255,255,.10);padding:18px;}}
.brand{{font-size:1.4rem;font-weight:500;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.12);margin-bottom:14px;}}
.sub{{background:rgba(0,0,0,.30);border-radius:14px;border:1px solid rgba(255,255,255,.07);padding:12px;margin-bottom:12px;}}
.slbl{{font-size:.70rem;color:rgba(255,255,255,.5);font-weight:500;text-transform:uppercase;letter-spacing:.5px;}}
.chip{{display:inline-block;padding:3px 11px;border-radius:20px;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-top:7px;background:{status_color}28;color:{status_color};border:1px solid {status_color};}}
.giant{{font-size:4.8rem;font-weight:300;line-height:.88;letter-spacing:-3px;}}
.giant sup{{font-size:1.6rem;font-weight:300;vertical-align:super;letter-spacing:0;}}
.pills{{display:flex;gap:8px;margin:14px 0;flex-wrap:wrap;}}
.pill{{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);border-radius:20px;padding:4px 13px;font-size:.83rem;color:#e1e2e6;}}
.headline{{font-size:1.9rem;font-weight:300;line-height:1.2;margin-top:12px;letter-spacing:-.3px;}}
.rlbl{{font-size:.70rem;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;}}
</style></head>
<body>
<div class="hero">
  <div class="grid">
    <div class="left">
      <div class="brand">🌀 LandfallReady</div>
      <div class="sub">
        <div class="slbl">Alert Status <span style="float:right;background:rgba(255,255,255,.12);padding:1px 7px;border-radius:8px;font-size:.70rem;">↑ {high_pct}%</span></div>
        <svg width="100%" height="44" viewBox="0 0 160 44">
          <defs><linearGradient id="ag" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#3498db"/>
            <stop offset="55%" stop-color="#f1c40f"/>
            <stop offset="100%" stop-color="#e74c3c"/>
          </linearGradient></defs>
          <path d="M 8 36 Q 50 36, 80 22 T 152 8" fill="none" stroke="url(#ag)" stroke-width="4" stroke-linecap="round"/>
          <circle cx="120" cy="13" r="5" fill="{status_color}" stroke="#fff" stroke-width="2"/>
        </svg>
        <div><span class="chip">{status_label}</span></div>
      </div>
      <div class="sub">
        <div class="slbl">Location</div>
        <div style="text-align:center;margin:8px 0;">
          <div style="width:44px;height:44px;border-radius:50%;background:radial-gradient(circle,rgba(52,152,219,.4),rgba(0,0,0,.6));margin:0 auto;display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.18);">
            <span style="font-size:1.2rem;">📍</span></div>
        </div>
        <div style="font-size:.78rem;color:rgba(255,255,255,.72);text-align:center;">{region_safe}</div>
      </div>
    </div>

    <div style="padding:2px 6px;">
      <div style="font-size:.88rem;color:rgba(255,255,255,.85);margin-bottom:12px;">📍 <strong>{region_safe}</strong> <span style="color:rgba(255,255,255,.5);">({today_str})</span></div>
      <div class="giant">{int(vmax)}<sup>km/h</sup></div>
      <div class="pills">
        <div class="pill">🌊 Surge {peak_flood:.1f}m</div>
        <div class="pill">🌧️ Rain {int(rain_mm)}mm</div>
        <div class="pill" style="background:{status_color}22;border-color:{status_color};color:{status_color};">{status_label}</div>
      </div>
      <div class="headline">{headline}</div>
      {wave_html}
    </div>

    <div style="padding:2px 0;">
      <div class="rlbl">Other Regions</div>
      {quick_btns}
    </div>
  </div>
</div>
</body></html>"""

    # Full-screen Streamlit layout override
    st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 0.4rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    max-width: 100% !important;
}
</style>""", unsafe_allow_html=True)

    components.html(hero_html, height=555, scrolling=False)
    st.markdown("---")

    # Native Streamlit controls row
    col_btn, col_lang, col_reg = st.columns([2, 1.2, 1.8])
    with col_btn:
        if st.button("🚀 Start Guided Tour", type="primary", use_container_width=True):
            st.session_state["guide_on"] = True
            st.toast("🔊 Audio guide enabled! Hover/click elements.", icon="🎤")
            st.rerun()
    with col_lang:
        langs = ["English", "Hindi", "Bengali", "Odia", "Telugu"]
        sel_lang = st.selectbox(
            "Language", langs,
            index=langs.index(st.session_state.get("lang", "English")),
            key="home_lang_pill", label_visibility="collapsed",
        )
        st.session_state["lang"] = sel_lang
    with col_reg:
        sel_reg = st.selectbox(
            "Region", list(REGIONS),
            index=list(REGIONS).index(region_name) if region_name in REGIONS else 0,
            key="home_region_selector", label_visibility="collapsed",
        )
        if sel_reg != region_name:
            st.session_state["selected_region"] = sel_reg
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Core Capabilities")
    card = ("background:rgba(18,24,38,.60);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);"
            "border-radius:18px;border:1px solid rgba(255,255,255,.09);padding:18px;height:100%;")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(f'<div style="{card}"><h3 style="color:#3498db;margin-top:0;">🌊 Predict Flood & Wind</h3>'
                    f'<p style="color:#dcdde1;font-size:.9rem;">72-hour spatial risk grid computing storm surge depth, '
                    f'exponential wind decay, and ground elevation flood susceptibility before landfall.</p></div>',
                    unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div style="{card}"><h3 style="color:#e67e22;margin-top:0;">🏥 Map Exposed Assets</h3>'
                    f'<p style="color:#dcdde1;font-size:.9rem;">OpenStreetMap Overpass spatial join tagging hospitals, '
                    f'shelters, power substations, and primary road submersion hazard zones.</p></div>',
                    unsafe_allow_html=True)
    with f3:
        st.markdown(f'<div style="{card}"><h3 style="color:#2ecc71;margin-top:0;">🤖 Gemini AI Advisory</h3>'
                    f'<p style="color:#dcdde1;font-size:.9rem;">Gemini Flash multimodal reasoning generating structured '
                    f'early-warning advisories in 5 regional Asian languages with audio guidance.</p></div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗺️ 4-Step Operational Workflow")
    w1, w2, w3, w4 = st.columns(4)
    steps = [
        ("1. Select Region & Scenario", "Choose landfall target and adjust wind & 72h rain sliders in the sidebar."),
        ("2. Inspect Spatial Risk Map", "View color-coded risk grid cells and exposed critical infrastructure overlay."),
        ("3. Generate AI Advisory", "Produce actionable emergency advisories for municipal disaster response teams."),
        ("4. Check Insurance Triggers", "Review automated pre-landfall micro-insurance liquidity payout tiers."),
    ]
    for col, (title, desc) in zip([w1, w2, w3, w4], steps):
        with col:
            st.markdown(
                f'<div style="{card}"><strong style="color:#f1f2f6;">{title}</strong><br>'
                f'<span style="font-size:.85rem;color:#a4b0be;">{desc}</span></div>',
                unsafe_allow_html=True,
            )
