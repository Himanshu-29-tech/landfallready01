"""CSS Styles & Frosted Glass Design Tokens matching the Weather Dashboard Mockup."""
import base64
import os
import streamlit as st


@st.cache_resource
def get_hero_bg_base64() -> str | None:
    """Load assets/cyclone.jpg or fallback webp image as Base64 Data URI."""
    paths = [
        os.path.join("assets", "cyclone.jpg"),
        os.path.join("assets", "cyclone.webp"),
        os.path.join("assets", "l56220260910181745_jpeg.webp"),
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                ext = p.split(".")[-1].lower()
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/webp"
                return f"data:{mime};base64,{b64}"
            except Exception:
                pass
    return None


def get_home_css() -> str:
    bg_uri = get_hero_bg_base64()
    if bg_uri:
        bg_style = f"background: linear-gradient(180deg, rgba(20, 24, 33, 0.52) 0%, rgba(15, 18, 25, 0.85) 100%), url('{bg_uri}') center/cover no-repeat;"
    else:
        bg_style = "background: linear-gradient(135deg, #121620 0%, #1c2333 50%, #0e121a 100%);"

    return f"""
    <style>
        .hero-wrapper {{
            {bg_style}
            border-radius: 36px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65);
            color: #f1f2f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        .glass-card-left {{
            background: rgba(30, 36, 48, 0.55);
            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 22px;
            height: 100%;
        }}

        .brand-title {{
            font-size: 1.6rem;
            font-weight: 500;
            color: #ffffff;
            margin-bottom: 18px;
            position: relative;
            display: inline-block;
        }}
        .brand-title::after {{
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 80%;
            height: 2px;
            background: linear-gradient(90deg, rgba(255,255,255,0.8), rgba(255,255,255,0.1));
            border-radius: 2px;
        }}

        .sub-card {{
            background: rgba(0, 0, 0, 0.35);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 14px;
            margin-bottom: 16px;
        }}

        .status-chip {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(230, 126, 34, 0.25);
            color: #e67e22;
            border: 1px solid rgba(230, 126, 34, 0.6);
            pointer-events: none;
        }}
        .status-Extreme {{ background: rgba(231,76,60,0.3) !important; color: #e74c3c !important; border-color: #e74c3c !important; }}
        .status-Dangerous {{ background: rgba(230,126,34,0.3) !important; color: #e67e22 !important; border-color: #e67e22 !important; }}
        .status-Elevated {{ background: rgba(241,196,15,0.3) !important; color: #f1c40f !important; border-color: #f1c40f !important; }}
        .status-Low {{ background: rgba(46,204,113,0.3) !important; color: #2ecc71 !important; border-color: #2ecc71 !important; }}

        .giant-temp {{
            font-size: 5.2rem;
            font-weight: 300;
            line-height: 0.9;
            color: #ffffff;
            letter-spacing: -3px;
        }}
        .giant-temp sup {{
            font-size: 2.2rem;
            font-weight: 300;
            top: -1.8rem;
            color: rgba(255,255,255,0.9);
        }}

        .pill-stat {{
            display: inline-flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.85rem;
            font-weight: 400;
            color: #e1e2e6;
            margin-right: 6px;
        }}

        .headline-banner {{
            font-size: 2.4rem;
            font-weight: 300;
            line-height: 1.15;
            color: #ffffff;
            margin: 18px 0;
            letter-spacing: -0.5px;
        }}

        .quick-region-item {{
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 12px 16px;
            margin-bottom: 12px;
            transition: all 0.25s ease;
        }}
        .quick-region-item:hover {{
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }}

        .wave-container {{
            margin-top: 25px;
            position: relative;
            padding-top: 10px;
        }}

        .time-header-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 400;
        }}

        .time-value-row {{
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
        }}
        .val-digit {{
            font-size: 1.6rem;
            font-weight: 300;
            color: rgba(255, 255, 255, 0.65);
        }}
        .val-digit-active {{
            font-size: 2.1rem;
            font-weight: 400;
            color: #ffffff;
            text-shadow: 0 0 12px rgba(255, 255, 255, 0.8);
        }}

        .glass-feature-card {{
            background: rgba(30, 36, 48, 0.5);
            backdrop-filter: blur(16px);
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            height: 100%;
        }}

        @media (max-width: 960px) {{
            .giant-temp {{
                font-size: 3.8rem;
            }}
            .headline-banner {{
                font-size: 1.8rem;
            }}
        }}
    </style>
    """
