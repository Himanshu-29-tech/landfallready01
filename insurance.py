"""Parametric Insurance trigger card module for early pre-landfall payout calculation."""
from __future__ import annotations


def evaluate_parametric_trigger(
    max_wind: float,
    rain_72h: float,
    wind_threshold: float = 140.0,
    rain_threshold: float = 200.0,
    base_sum_insured_inr: float = 50000.0,
) -> dict:
    """Compute parametric trigger tier and illustrative payout per household."""
    wind_exceeded = max_wind >= wind_threshold
    rain_exceeded = rain_72h >= rain_threshold

    if max_wind >= (1.25 * wind_threshold) and rain_72h >= (1.25 * rain_threshold):
        payout_pct = 100
        tier_name = "🔴 Catastrophic (Tier 3 - 100% Payout)"
        status_color = "#e74c3c"
        description = "Extreme compound wind speed and rainfall intensity exceeded 125% of trigger thresholds. Maximum emergency liquidity payout unlocked."
    elif wind_exceeded and rain_exceeded:
        payout_pct = 50
        tier_name = "🟠 Major Compound Event (Tier 2 - 50% Payout)"
        status_color = "#e67e22"
        description = "Both wind speed and 72h accumulated rainfall breached parametric triggers simultaneously. Substantial payout unlocked."
    elif wind_exceeded or rain_exceeded:
        payout_pct = 25
        tier_name = "🟡 Partial Breach (Tier 1 - 25% Payout)"
        status_color = "#f1c40f"
        breached_param = "Wind Speed" if wind_exceeded else "72h Rainfall"
        description = f"Single parameter trigger breached ({breached_param}). Early liquidity disbursement unlocked for early response."
    else:
        payout_pct = 0
        tier_name = "🟢 Below Trigger Threshold (Tier 0 - 0% Payout)"
        status_color = "#2ecc71"
        description = "Meteorological parameters remain below parametric policy triggers. No insurance payout triggered."

    payout_per_hh = (payout_pct / 100.0) * base_sum_insured_inr

    return {
        "tier_name": tier_name,
        "payout_pct": payout_pct,
        "payout_per_hh_inr": payout_per_hh,
        "status_color": status_color,
        "description": description,
        "wind_exceeded": wind_exceeded,
        "rain_exceeded": rain_exceeded,
        "max_wind": max_wind,
        "rain_72h": rain_72h,
        "wind_threshold": wind_threshold,
        "rain_threshold": rain_threshold,
        "base_sum_insured": base_sum_insured_inr,
    }
