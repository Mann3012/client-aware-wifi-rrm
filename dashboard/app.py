"""
WiFi RRM Digital Twin — Streamlit Dashboard
============================================
Two frontends exist in this project:
  1. dashboard/app.py      ← this file (Streamlit, port 8501)
  2. frontend/             ← React/Vite app (port 5173)

Both consume the same FastAPI backend on port 8000.
"""

import os
import math
import requests
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_URL  = f"http://{API_HOST}:{API_PORT}"

# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WiFi RRM Digital Twin",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Page Header ── */
.pg-header {
    font-size: 2rem; font-weight: 800; color: #0F172A;
    letter-spacing: -0.5px; line-height: 1.2; margin-bottom: 0.1rem;
}
.pg-sub {
    font-size: 0.95rem; color: #64748B; font-weight: 400; margin-bottom: 1.6rem;
}

/* ── AP Health Cards ── */
.hcard {
    padding: 1rem 1.2rem; border-radius: 10px; margin-bottom: 0.6rem;
    border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.hcard-ok   { background:#ECFDF5; border-left:5px solid #10B981; }
.hcard-warn { background:#FFFBEB; border-left:5px solid #F59E0B; }
.hcard-crit { background:#FEF2F2; border-left:5px solid #EF4444; }
.hcard-title{ font-weight:700; font-size:1rem; color:#1E293B; }
.mlabel     { font-size:0.8rem; color:#64748B; font-weight:500; }

/* ── Causal Chain Report ── */
.cc-wrap {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 0.5rem;
}

/* gradient report header */
.cc-header {
    background: linear-gradient(135deg, #0F2C5C 0%, #1D4ED8 60%, #2563EB 100%);
    color: #fff;
    padding: 1.1rem 1.4rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.cc-header-title {
    font-size: 1.15rem; font-weight: 800; letter-spacing: -0.3px;
}
.cc-header-meta {
    font-size: 0.78rem; opacity: 0.78; font-weight: 400;
}

/* section card */
.cc-section {
    border-left: 4px solid;
    border-radius: 8px;
    padding: 0.85rem 1rem 0.85rem 1.1rem;
    margin: 0.55rem 0;
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.cc-env   { border-color: #3B82F6; }
.cc-prop  { border-color: #8B5CF6; }
.cc-rf    { border-color: #0891B2; }
.cc-net   { border-color: #D97706; }
.cc-qoe   { border-color: #DB2777; }
.cc-root  { border-color: #DC2626; }
.cc-rec   { border-color: #16A34A; }
.cc-impact{ border-color: #059669; }

.cc-sec-title {
    font-size: 0.9rem; font-weight: 700; margin-bottom: 0.55rem;
    display: flex; align-items: center; gap: 0.35rem;
}

/* metric rows inside sections */
.mrow {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 0.2rem 0; border-bottom: 1px solid #F1F5F9; font-size: 0.84rem;
    gap: 0.5rem;
}
.mrow:last-of-type { border-bottom: none; }
.mk { color: #64748B; font-weight: 500; white-space: nowrap; }
.mv { font-family: 'JetBrains Mono', monospace; font-weight: 600;
      color: #0F172A; text-align: right; }
.mv-g { color: #16A34A; }
.mv-y { color: #D97706; }
.mv-r { color: #DC2626; }

/* formula box */
.fbox {
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 6px; padding: 0.5rem 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.79rem; color: #1E40AF; margin: 0.45rem 0;
    line-height: 1.7;
}

/* SNR threshold badges */
.badge {
    display: inline-block; padding: 0.1rem 0.45rem;
    border-radius: 999px; font-size: 0.7rem; font-weight: 700;
}
.b-g  { background:#DCFCE7; color:#15803D; border:1px solid #86EFAC; }
.b-y  { background:#FEF9C3; color:#92400E; border:1px solid #FDE68A; }
.b-r  { background:#FEE2E2; color:#991B1B; border:1px solid #FCA5A5; }
.b-bl { background:#DBEAFE; color:#1E40AF; border:1px solid #93C5FD; }

/* root cause pill */
.rc-pill {
    display: inline-block; background: #FEE2E2; color: #991B1B;
    border: 1px solid #FCA5A5; border-radius: 999px;
    padding: 0.2rem 0.9rem; font-weight: 700; font-size: 0.86rem;
}

/* confidence bar */
.conf-track {
    background: #E2E8F0; border-radius: 999px; height: 9px; overflow: hidden; margin-top: 0.4rem;
}
.conf-fill { height: 9px; border-radius: 999px; }

/* justification box */
.jbox {
    background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px;
    padding: 0.7rem 1rem; font-size: 0.86rem; color: #14532D;
    line-height: 1.75; font-style: italic; margin-top: 0.4rem;
}

/* impact rows */
.irow {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.28rem 0; border-bottom: 1px solid #F1F5F9; font-size: 0.84rem;
}
.irow:last-of-type { border-bottom: none; }

/* causal arrow divider */
.cc-arrow {
    text-align: center; color: #94A3B8; font-size: 0.72rem;
    font-weight: 600; margin: 0.05rem 0; letter-spacing: 0.4px;
}

/* inner padding wrapper */
.cc-body { padding: 0.65rem 1rem 0.9rem; }

/* "Explain" button hint */
.explain-hint {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: linear-gradient(135deg,#1D4ED8,#3B82F6);
    color:#fff; border-radius:8px; padding:0.4rem 0.9rem;
    font-weight:700; font-size:0.82rem; margin-bottom:0.6rem;
    box-shadow: 0 2px 8px rgba(59,130,246,0.35);
}

/* old explain-panel style kept for tab1 */
.explain-panel {
    background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:1rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# API Helpers
# ─────────────────────────────────────────────────────────────────────────────
def fetch_from_api(endpoint: str, params: dict = None) -> list:
    try:
        r = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        return r.json() if r.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        return []

def set_scenario(ap_id: str, scenario_name: str):
    try:
        requests.post(f"{API_URL}/scenario/set",
                      params={"ap_id": ap_id, "scenario_name": scenario_name}, timeout=5)
    except Exception:
        pass

def trigger_simulator_step() -> bool:
    try:
        res = requests.post(f"{API_URL}/simulator/trigger", timeout=5)
        return res.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Causal Chain Physics Engine
# All formulas directly mirror src/realistic_simulator/telemetry_simulator.py
# ─────────────────────────────────────────────────────────────────────────────

def compute_path_loss(distance_m, freq_mhz, wall_loss_db):
    """
    Log-Distance Indoor Path Loss (n=3) + wall attenuation.
    Source: src/realistic_simulator/telemetry_simulator.py → calculate_path_loss()

    PL(d0=1m) = 32.44 + 20·log10(0.001 km) + 20·log10(freq_MHz)
    PL(d)     = PL(d0) + 10·3.0·log10(d / 1m) + wall_loss
    """
    if distance_m is None or freq_mhz is None:
        return None
    d     = max(1.0, float(distance_m))
    pl_d0 = 32.44 + 20 * math.log10(0.001) + 20 * math.log10(float(freq_mhz))
    pl_d  = pl_d0 + 10 * 3.0 * math.log10(d) + float(wall_loss_db or 0)
    return round(pl_d, 1)


def get_snr_label(snr):
    """SNR quality tier per 802.11 standards."""
    if snr is None:
        return "Unknown", "b-bl"
    if snr > 25:
        return "Excellent  (> 25 dB)", "b-g"
    if snr >= 20:
        return "Good  (20 – 25 dB)", "b-g"
    if snr >= 10:
        return "Moderate  (10 – 20 dB)", "b-y"
    return "Poor  (< 10 dB)", "b-r"


def get_modulation(snr):
    """Estimate 802.11 modulation from SNR."""
    if snr is None:
        return "Unknown"
    if snr > 28:
        return "1024-QAM / 256-QAM  (MCS 10–11)"
    if snr > 22:
        return "256-QAM  (MCS 8–9)"
    if snr > 18:
        return "64-QAM  (MCS 7)"
    if snr > 13:
        return "16-QAM  (MCS 4–5)"
    if snr > 8:
        return "QPSK  (MCS 2–3)"
    return "BPSK  (MCS 0–1)"


def derive_root_cause_ranked(rssi, snr, noise_floor, retry_rate, airtime_frac, int_type, distance_m):
    """
    Returns a ranked list of potential root causes with confidence scores.
    """
    causes = []
    
    if int_type and "Bluetooth" in int_type:
        causes.append({"label": "Interference (Bluetooth)", "conf": 0.95, "reason": "Bursty non-WiFi interference detected; overlaps with Wi-Fi frames."})
    elif int_type and "Microwave" in int_type:
        causes.append({"label": "Interference (Microwave)", "conf": 0.95, "reason": "Broadband RF noise emission detected."})
    elif int_type and "Neighbor" in int_type:
        causes.append({"label": "Co-Channel Contention (Neighbor AP)", "conf": 0.92, "reason": "Neighbor AP traffic increases contention and airtime competition."})
    elif int_type and int_type not in ("None", "none", ""):
        causes.append({"label": f"Interference ({int_type})", "conf": 0.90, "reason": "Active non-WiFi interference detected."})
    elif noise_floor is not None and noise_floor >= -90:
        causes.append({"label": "Interference (Elevated Noise)", "conf": 0.85, "reason": "Elevated noise floor independent of client traffic."})
    else:
        causes.append({"label": "Interference", "conf": 0.15, "reason": "Noise floor is clean at the AP."})
        
    if rssi is not None and rssi < -78:
        if distance_m is not None and distance_m > 20:
            causes.append({"label": "Coverage (Distance + Path Loss)", "conf": 0.90, "reason": "Weak signal due to propagation distance and path loss."})
        else:
            causes.append({"label": "Coverage (Weak Signal)", "conf": 0.88, "reason": "Weak signal despite proximity (possible obstruction)."})
    else:
        causes.append({"label": "Coverage", "conf": 0.18, "reason": "RSSI remains strong, suggesting adequate signal propagation."})
        
    if airtime_frac is not None and airtime_frac > 0.75:
        causes.append({"label": "Congestion (High Density)", "conf": 0.93, "reason": "Channel is heavily utilized by active traffic, causing medium contention."})
    else:
        causes.append({"label": "Congestion", "conf": 0.20, "reason": "Airtime utilization is nominal, indicating no channel saturation."})

    causes.sort(key=lambda x: x["conf"], reverse=True)
    
    if causes[0]["conf"] < 0.50:
        causes.insert(0, {"label": "System Optimal", "conf": 0.99, "reason": "All metrics are within healthy nominal parameters."})
        
    return causes


def derive_root_cause(rssi, snr, noise_floor, retry_rate, airtime_frac, int_type, distance_m):
    """
    Heuristic root cause matching recommendation_engine.py decision rules.
    Returns (cause_label, confidence_float).
    """
    if int_type and int_type not in ("None", "none", ""):
        return f"Interference Issue ({int_type})", 0.95
    if noise_floor is not None and noise_floor >= -90:
        return "Interference Issue (Elevated Noise Floor)", 0.92
    if rssi is not None and rssi < -78:
        if distance_m is not None and distance_m > 20:
            return "Coverage Issue (Distance + Path Loss)", 0.90
        return "Coverage Issue (Weak Signal)", 0.88
    if snr is not None and snr < 10:
        return "Coverage / Noise Issue (Low SNR)", 0.87
    if airtime_frac is not None and airtime_frac > 0.75:
        return "Congestion Issue (High Airtime Utilization)", 0.85
    if retry_rate is not None and retry_rate > 0.20:
        return "Capacity Issue (High Retry Rate)", 0.82
    if distance_m is not None and distance_m > 22:
        return "Obstruction / Distance Issue", 0.80
    return "System Optimal — No Dominant Issue", 1.0


def build_justification_text(action, rssi, snr, noise_floor, distance_m,
                              wall_count, retry_rate, qoe_score, int_type, airtime_frac):
    """
    Generates an engineer-grade narrative justification for the selected action.
    Incorporates detailed wireless networking physics, SNR classifications,
    interference types, network performance degradation effects, adaptive data rates,
    and root cause reasoning with explicit rejection of competing causes.
    """
    # Format inputs safely
    r_val = rssi if rssi is not None else -95.0
    s_val = snr if snr is not None else 0.0
    nf_val = noise_floor if noise_floor is not None else -95.0
    d_val = distance_m if distance_m is not None else 1.0
    w_count = wall_count if wall_count is not None else 0
    w_loss = w_count * 3.0
    ret_rate = retry_rate if retry_rate is not None else 0.0
    qoe = qoe_score if qoe_score is not None else 0.0
    airtime = airtime_frac if airtime_frac is not None else 0.0
    interference = int_type if (int_type and int_type not in ("None", "")) else "None"

    # 1. RSSI Explanation
    rssi_explanation = (
        f"The Received Signal Strength Indicator (RSSI) is measured at {r_val:.1f} dBm. "
        f"In RF engineering, RSSI represents the received signal power in dBm, where values closer to 0 dBm indicate "
        f"stronger signals. The RSSI is attenuated from the transmitter's power by Free Space Path Loss (FSPL) "
        f"as RF energy spreads spherically over a propagation distance of {d_val:.1f} m, compounded by "
        f"additional signal attenuation of {w_loss:.1f} dB introduced by {w_count} wall obstacles."
    )

    # 2. SNR & Noise Floor Calculation and Classification
    snr_calc = f"SNR = RSSI - Noise Floor = {r_val:.1f} dBm - ({nf_val:.1f} dBm) = {s_val:.1f} dB."
    
    if s_val > 25:
        snr_tier = "Excellent (>25 dB)"
    elif s_val >= 20:
        snr_tier = "Good (20–25 dB)"
    elif s_val >= 10:
        snr_tier = "Moderate (10–20 dB)"
    else:
        snr_tier = "Poor (<10 dB)"

    snr_explanation = (
        f"The resulting Signal-to-Noise Ratio (SNR) is {s_val:.1f} dB, which is classified as {snr_tier}. "
        f"The Noise Floor represents the background RF energy and active interference. "
        f"An elevated noise floor reduces the effective SNR even when the RSSI remains unchanged, "
        f"which narrows the signal margins required for reliable decoding."
    )

    # 3. Adaptive Data Rates & Network Performance
    performance_explanation = (
        f"Under poor RF conditions, wireless devices dynamically reduce modulation and coding rates (MCS) "
        f"using Adaptive Data Rates / Dynamic Rate Shifting (DRS) to maintain reliable delivery. "
        f"While a strong SNR supports higher modulation efficiency (e.g., 256-QAM or 1024-QAM) and higher throughput, "
        f"a weak SNR forces a fallback to lower modulation efficiency (e.g., QPSK or BPSK) for reliable delivery, "
        f"resulting in lower throughput. At {s_val:.1f} dB SNR, retry rates rise to {ret_rate*100:.1f}%, increasing packet corruption, "
        f"airtime consumption, and latency, which ultimately degrades the Quality of Experience (QoE) to {qoe:.1f}/10."
    )

    # 4. Root Cause Reasoning & Rejection of Competing Causes
    if action == "POWER_INCREASE":
        dominant_issue = "Coverage / Obstruction"
        reasons = (
            f"RSSI is degraded to {r_val:.1f} dBm due to propagation distance and wall attenuation. "
            f"We reject Interference as a dominant cause because the noise floor remains stable at a clean baseline of {nf_val:.1f} dBm. "
            f"We reject Congestion / Capacity because airtime utilization is nominal at {airtime*100:.1f}%, indicating no channel saturation."
        )
        recommendation_action_desc = "Increasing the AP transmit power compensates for path loss, raising the RSSI and restoring the SNR above 20 dB."
    elif action == "CHANNEL_CHANGE":
        dominant_issue = "Interference"
        if interference == "MICROWAVE":
            int_desc = "Non-WiFi interference from a Microwave oven burst"
        elif interference == "BLUETOOTH":
            int_desc = "Non-WiFi interference from a Bluetooth storm"
        elif interference == "CO_CHANNEL_INTERFERENCE" or interference == "Neighbor AP":
            int_desc = "Co-Channel Interference (CCI) from multiple APs sharing the same channel, increasing contention and airtime competition"
        elif interference == "ADJACENT_CHANNEL":
            int_desc = "Neighbor Channel Interference (NCI) from overlapping adjacent channel overlap"
        else:
            int_desc = f"interference ({interference})"

        reasons = (
            f"The dominant issue is {dominant_issue} caused by {int_desc}, raising the noise floor to {nf_val:.1f} dBm and reducing SNR. "
            f"We reject Coverage / Obstruction because RSSI is strong at {r_val:.1f} dBm, meaning the physical signal propagation is adequate. "
            f"We reject Congestion as the primary root cause because retry rates are driven by noise-induced corruption rather than pure channel contention."
        )
        recommendation_action_desc = "Migrating to a clean channel lowers the effective noise floor, recovering SNR and restoring modulation efficiency."
    elif action == "LOAD_BALANCE":
        dominant_issue = "Congestion"
        reasons = (
            f"The dominant issue is {dominant_issue} caused by high client density, which increases channel contention, collision probability, "
            f"and retry rates while airtime utilization rises to {airtime*100:.1f}%. "
            f"We reject Coverage / Obstruction because RSSI ({r_val:.1f} dBm) and SNR ({s_val:.1f} dB) are healthy. "
            f"We reject Interference because the noise floor is clean at {nf_val:.1f} dBm."
        )
        recommendation_action_desc = "Steering excess clients to adjacent APs or other frequency bands reduces contention and airtime utilization."
    elif action == "WIDTH_ADJUST":
        dominant_issue = "Congestion / Capacity"
        reasons = (
            f"The dominant issue is {dominant_issue}. Operating on a wide channel increases collision probability and capture of adjacent noise. "
            f"We reject pure Coverage issues because the RSSI of {r_val:.1f} dBm is acceptable."
        )
        recommendation_action_desc = "Narrowing the channel width reduces the noise integration bandwidth, improving SNR margin and link stability under congestion."
    elif action == "POWER_DECREASE":
        dominant_issue = "Capacity"
        reasons = (
            f"The dominant issue is overlapping cell coverage causing excessive co-channel overlap. "
            f"We reject Coverage because RSSI is strong at {r_val:.1f} dBm. We reject external interference as the background noise floor is stable."
        )
        recommendation_action_desc = "Reducing TX power shrinks the cell boundary, reducing co-channel interference and improving overall spectral reuse."
    else:
        dominant_issue = "System Optimal"
        reasons = (
            f"RSSI ({r_val:.1f} dBm), Noise Floor ({nf_val:.1f} dBm), SNR ({s_val:.1f} dB), and airtime utilization ({airtime*100:.1f}%) "
            f"are all within healthy nominal parameters."
        )
        recommendation_action_desc = "No corrective RRM actions are required at this time."

    root_cause_explanation = (
        f"ROOT CAUSE DETERMINATION:\n"
        f"Dominant Issue identified: **{dominant_issue}**\n"
        f"Causal Reasoning: {reasons}\n"
        f"RRM Action Justification: {recommendation_action_desc}"
    )

    # Combine into unified senior wireless engineer troubleshooting log
    report = (
        f"ENGINEERING TROUBLESHOOTING NOTES:\n\n"
        f"• Propagation & Path Loss:\n{rssi_explanation}\n\n"
        f"• RF Signal Quality:\n{snr_calc}\n{snr_explanation}\n\n"
        f"• Adaptive Data Rates & Network Impact:\n{performance_explanation}\n\n"
        f"• Causal Diagnostics:\n{root_cause_explanation}"
    )
    return report


def estimate_post_action_impact(action, rssi, snr, qoe, retry_rate):
    """
    Predicts approximate metric improvements after the recommended action.
    Delta values are conservative engineering estimates per action type.
    """
    deltas = {
        "CHANNEL_CHANGE":  dict(rssi= 1, snr=10, qoe=2.5, retry=-0.20),
        "POWER_INCREASE":  dict(rssi= 6, snr= 6, qoe=1.8, retry=-0.12),
        "POWER_DECREASE":  dict(rssi=-4, snr= 5, qoe=1.2, retry=-0.10),
        "WIDTH_ADJUST":    dict(rssi= 0, snr= 4, qoe=1.0, retry=-0.08),
        "LOAD_BALANCE":    dict(rssi= 0, snr= 3, qoe=1.5, retry=-0.10),
        "NONE":            dict(rssi= 0, snr= 0, qoe=0.0, retry= 0.00),
    }.get(action, dict(rssi=0, snr=0, qoe=0, retry=0))

    def safe_add(v, delta, mn=None, mx=None):
        if v is None:
            return None
        r = round(v + delta, 2)
        if mn is not None: r = max(mn, r)
        if mx is not None: r = min(mx, r)
        return r

    return {
        "rssi_before":  rssi,
        "rssi_after":   safe_add(rssi,       deltas["rssi"]),
        "snr_before":   snr,
        "snr_after":    safe_add(snr,        deltas["snr"], mn=0),
        "qoe_before":   qoe,
        "qoe_after":    safe_add(qoe,        deltas["qoe"], mx=10),
        "retry_before": retry_rate,
        "retry_after":  safe_add(retry_rate, deltas["retry"], mn=0, mx=1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HTML Color Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _cv(v, decimals=1, suffix="", fallback="—"):
    """Convert value to display string."""
    if v is None:
        return fallback
    return f"{round(float(v), decimals)}{suffix}"

def _rssi_cls(v):
    if v is None: return "mv"
    if v >= -65:  return "mv mv-g"
    if v >= -78:  return "mv mv-y"
    return "mv mv-r"

def _snr_cls(v):
    if v is None: return "mv"
    if v >= 20:   return "mv mv-g"
    if v >= 10:   return "mv mv-y"
    return "mv mv-r"

def _noise_cls(v):
    if v is None:  return "mv"
    if v < -90:    return "mv mv-g"
    if v < -80:    return "mv mv-y"
    return "mv mv-r"

def _retry_cls(pct):
    if pct is None: return "mv"
    if pct < 10:    return "mv mv-g"
    if pct < 20:    return "mv mv-y"
    return "mv mv-r"

def _airtime_cls(pct):
    if pct is None: return "mv"
    if pct < 60:    return "mv mv-g"
    if pct < 80:    return "mv mv-y"
    return "mv mv-r"

def _qoe_cls(v):
    if v is None: return "mv"
    if v >= 7:    return "mv mv-g"
    if v >= 4:    return "mv mv-y"
    return "mv mv-r"

def _dist_cls(v):
    if v is None: return "mv"
    if v < 12:    return "mv mv-g"
    if v < 22:    return "mv mv-y"
    return "mv mv-r"

def _pl_cls(v):
    if v is None: return "mv"
    if v < 70:    return "mv mv-g"
    if v < 85:    return "mv mv-y"
    return "mv mv-r"

def _mrow(label, value_html):
    return f'<div class="mrow"><span class="mk">{label}</span><span>{value_html}</span></div>'

def _arrow(label):
    return f'<div class="cc-arrow">↓ &nbsp; {label} &nbsp; ↓</div>'

def _delta_html(before, after, suffix="", higher_is_better=True):
    """Render a coloured delta between before and after values."""
    if before is None or after is None:
        return ""
    d    = after - before
    pos  = d > 0
    good = pos if higher_is_better else not pos
    col  = "#16A34A" if good else "#DC2626"
    sign = "+" if d > 0 else ""
    arr  = "↑" if d > 0 else "↓"
    return (f' <span style="color:{col};font-weight:700;font-size:0.8rem;">'
            f'{arr} {sign}{round(d, 2)}{suffix}</span>')

def _conf_color(c):
    if c >= 0.85: return "#22C55E"
    if c >= 0.65: return "#F59E0B"
    return "#EF4444"


# ─────────────────────────────────────────────────────────────────────────────
# Main Causal Chain HTML Renderer
# ─────────────────────────────────────────────────────────────────────────────
def render_causal_chain_html(latest_row: dict, top_rec: dict, ap_id: str) -> str:
    """
    Builds the full 8-layer causal chain HTML report.

    Layer order (mirrors the causal physics pipeline in telemetry_simulator.py):
      ① Environment Factors
      ② Propagation Analysis
      ③ RF Signal Quality
      ④ Network Impact
      ⑤ User Experience (QoE)
      ⑥ Root Cause Detection
      ⑦ Recommendation Justification
      ⑧ Predicted Impact
    """

    # ── Extract all telemetry fields ─────────────────────────────────────────
    distance_m   = latest_row.get("distance")
    max_dist_m   = latest_row.get("max_distance")
    closest_m    = latest_row.get("closest_client")
    wall_count   = latest_row.get("wall_count")
    wall_loss_db = latest_row.get("wall_loss")
    freq_mhz     = latest_row.get("freq_mhz")    or 5180.0
    tx_power_dbm = latest_row.get("tx_power")    or 20.0
    airtime_frac = latest_row.get("airtime_utilization")  # 0.0–1.0
    int_type     = latest_row.get("interference_type") or "None"
    client_count = latest_row.get("client_count")
    channel      = latest_row.get("channel")
    scenario_nm  = latest_row.get("scenario_name", "Unknown")

    rssi_dbm     = latest_row.get("rssi")
    noise_dbm    = latest_row.get("noise_floor")
    snr_db       = latest_row.get("snr")
    retry_frac   = latest_row.get("retry_rate")   # 0.0–1.0
    qoe_score    = latest_row.get("qoe_score")
    qoe_cat      = latest_row.get("qoe_category") or "—"

    # ── Recommendation fields ─────────────────────────────────────────────────
    action       = (top_rec.get("action")       or "NONE") if top_rec else "NONE"
    confidence   = (top_rec.get("confidence")   or 0.80)   if top_rec else 0.80
    rc_from_rec  = (top_rec.get("root_cause")   or "")     if top_rec else ""
    exp_gain     = (top_rec.get("expected_qoe_gain") or 0) if top_rec else 0
    cur_val      = (top_rec.get("current_value")     or "—") if top_rec else "—"
    rec_val      = (top_rec.get("recommended_value") or "—") if top_rec else "—"
    rec_reason   = (top_rec.get("reason")        or "")    if top_rec else ""

    # ── Derived values ────────────────────────────────────────────────────────
    path_loss_db  = compute_path_loss(distance_m, freq_mhz, wall_loss_db)
    est_rx_pwr    = (round(tx_power_dbm - path_loss_db, 1)
                     if path_loss_db is not None else None)

    # SNR formula string  (formula from telemetry_simulator.py → calculate_snr)
    if rssi_dbm is not None and noise_dbm is not None:
        snr_formula = (f"{rssi_dbm:.1f} &minus; ({noise_dbm:.1f}) "
                       f"= <strong>{snr_db:.1f} dB</strong>")
    else:
        snr_formula = "Insufficient data"

    snr_label, snr_badge_cls = get_snr_label(snr_db)
    mod_scheme  = get_modulation(snr_db)

    # Percentage versions of fraction metrics
    retry_pct     = round(retry_frac * 100,  1) if retry_frac  is not None else None
    airtime_pct   = round(airtime_frac * 100, 1) if airtime_frac is not None else None

    # Heuristic estimates
    pkt_loss_pct  = round(retry_pct * 0.70, 1) if retry_pct is not None else None
    thput_deg_pct = round(retry_pct * 1.50, 1) if retry_pct is not None else None
    latency_ms    = round(retry_pct * 1.20, 0) if retry_pct is not None else None

    # Root cause
    if rc_from_rec and rc_from_rec not in ("NONE", "None", ""):
        root_cause_label = rc_from_rec.replace("_", " ").title()
        root_conf = confidence
    else:
        root_cause_label, root_conf = derive_root_cause(
            rssi_dbm, snr_db, noise_dbm, retry_frac, airtime_frac, int_type, distance_m
        )

    conf_pct = int(root_conf * 100)
    conf_col = _conf_color(root_conf)

    # Justification paragraph
    justification = build_justification_text(
        action, rssi_dbm, snr_db, noise_dbm, distance_m,
        wall_count, retry_frac, qoe_score, int_type, airtime_frac
    )

    # Post-action impact predictions
    impact = estimate_post_action_impact(action, rssi_dbm, snr_db, qoe_score, retry_frac)

    if action == "NONE":
        impact_html = "<p style='color:#64748B;font-size:0.86rem;margin:0;'>System is already operating optimally — no action needed.</p>"
    else:
        impact_html = f"""
    <div class="irow">
      <span class="mk">RSSI</span>
      <span>
        <span class="mv">{_cv(impact['rssi_before'], 1, ' dBm')}</span>
        &nbsp;&rarr;&nbsp;
        <span class="mv mv-g">{_cv(impact['rssi_after'], 1, ' dBm')}</span>
        {_delta_html(impact['rssi_before'], impact['rssi_after'], ' dBm', higher_is_better=True)}
      </span>
    </div>
    <div class="irow">
      <span class="mk">SNR</span>
      <span>
        <span class="mv">{_cv(impact['snr_before'], 1, ' dB')}</span>
        &nbsp;&rarr;&nbsp;
        <span class="mv mv-g">{_cv(impact['snr_after'], 1, ' dB')}</span>
        {_delta_html(impact['snr_before'], impact['snr_after'], ' dB', higher_is_better=True)}
      </span>
    </div>
    <div class="irow">
      <span class="mk">QoE Score</span>
      <span>
        <span class="mv">{_cv(impact['qoe_before'], 1, ' / 100')}</span>
        &nbsp;&rarr;&nbsp;
        <span class="mv mv-g">{_cv(impact['qoe_after'], 1, ' / 100')}</span>
        {_delta_html(impact['qoe_before'], impact['qoe_after'], ' pts', higher_is_better=True)}
      </span>
    </div>
    <div class="irow">
      <span class="mk">Retry Rate</span>
      <span>
        <span class="mv">{_cv((impact['retry_before'] or 0)*100, 1, ' %')}</span>
        &nbsp;&rarr;&nbsp;
        <span class="mv mv-g">{_cv((impact['retry_after'] or 0)*100, 1, ' %')}</span>
        {_delta_html(impact['retry_before'], impact['retry_after'], ' pts', higher_is_better=False)}
      </span>
    </div>
    """

    # Timestamp
    now_ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # ── Interference display ──────────────────────────────────────────────────
    int_clean     = int_type not in ("None", "none", "", None)
    int_cls       = "mv mv-r" if int_clean else "mv mv-g"
    int_display   = int_type if int_clean else "None — Clean RF Environment"

    # ── Wall display ──────────────────────────────────────────────────────────
    wc_display = wall_count if wall_count is not None else "—"
    wl_display = _cv(wall_loss_db, 1, " dB")

    # ─────────────────────────────────────────────────────────────────────────
    # Assemble HTML
    # ─────────────────────────────────────────────────────────────────────────
    html = f"""
<div class="cc-wrap">

  <!-- ══ REPORT HEADER ══ -->
  <div class="cc-header">
    <div class="cc-header-title">🔗 &nbsp; Causal Metric Chain &mdash; Engineering Report</div>
    <div class="cc-header-meta">
      AP: <strong>{ap_id}</strong> &nbsp;|&nbsp;
      Scenario: <em>{scenario_nm}</em> &nbsp;|&nbsp;
      Channel: {channel or "—"} &nbsp;|&nbsp;
      Action: <strong>{action}</strong> &nbsp;|&nbsp;
      Generated: {now_ts}
    </div>
  </div>

  <div class="cc-body">

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ① — Environment Factors             -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-env">
    <div class="cc-sec-title" style="color:#1D4ED8;">
      ① &nbsp; 🌍 &nbsp; Environment Factors
    </div>

    {_mrow("Client Distance (average)",
           f'<span class="{_dist_cls(distance_m)}">{_cv(distance_m, 1, " m")}</span>')}

    {_mrow("Client Distance (closest / furthest)",
           f'<span class="mv">{_cv(closest_m, 1, " m")} &nbsp;/&nbsp; {_cv(max_dist_m, 1, " m")}</span>')}

    {_mrow("Walls / Obstacles",
           f'<span class="mv">{wc_display} wall(s)</span>'
           f'&nbsp;<span class="mv mv-y">&rarr; {wl_display} total attenuation</span>')}

    {_mrow("Interference Source",
           f'<span class="{int_cls}">{int_display}</span>')}

    {_mrow("Channel Utilization (Airtime)",
           f'<span class="{_airtime_cls(airtime_pct)}">{_cv(airtime_pct, 1, " %")}</span>')}

    {_mrow("Connected Clients",
           f'<span class="mv">{client_count if client_count is not None else "—"}</span>')}

    {_mrow("Operating Frequency",
           f'<span class="mv">{_cv(freq_mhz, 0, " MHz")}</span>')}

    {_mrow("AP Transmit Power",
           f'<span class="mv">{_cv(tx_power_dbm, 0, " dBm")}</span>')}
  </div>

  {_arrow("client distance + walls + interference → path loss")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ② — Propagation Analysis            -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-prop">
    <div class="cc-sec-title" style="color:#7C3AED;">
      ② &nbsp; 📡 &nbsp; Propagation Analysis
    </div>

    {_mrow("Path Loss Model",
           '<span class="mv">Log-Distance Indoor (path-loss exponent n = 3.0)</span>')}

    {_mrow("Reference loss PL(d₀ = 1 m)",
           f'<span class="mv">'
           f'{round(32.44 + 20*math.log10(0.001) + 20*math.log10(float(freq_mhz)), 1) if freq_mhz else "—"}'
           f' dB</span>')}

    {_mrow("Wall Attenuation  (3.0 dB / wall)",
           f'<span class="mv mv-y">{wl_display}'
           f'  ({wc_display} × 3.0 dB)</span>')}

    {_mrow("Total Computed Path Loss",
           f'<span class="{_pl_cls(path_loss_db)}">{_cv(path_loss_db, 1, " dB")}</span>')}

    {_mrow("Estimated Received Power  (TX − PL)",
           f'<span class="{_rssi_cls(est_rx_pwr)}">{_cv(est_rx_pwr, 1, " dBm")}</span>')}

    <div class="fbox">
      PL(d₀=1m) = 32.44 + 20&middot;log&#8321;&#8320;(0.001&nbsp;km)
                  + 20&middot;log&#8321;&#8320;({_cv(freq_mhz, 0)}&nbsp;MHz)
      <br>
      PL(d)     = PL(d₀) + 10 &times; 3.0 &times; log&#8321;&#8320;({_cv(distance_m, 1)}m / 1m)
                  + {wl_display} wall loss
                  = <strong>{_cv(path_loss_db, 1, " dB")}</strong>
      <br>
      Received   = TX ({_cv(tx_power_dbm, 0, " dBm")})
                   &minus; PL ({_cv(path_loss_db, 1, " dB")})
                   = <strong>{_cv(est_rx_pwr, 1, " dBm")}</strong>
    </div>
  </div>

  {_arrow("path loss reduces received signal → RSSI degradation")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ③ — RF Signal Quality               -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-rf">
    <div class="cc-sec-title" style="color:#0891B2;">
      ③ &nbsp; 📶 &nbsp; RF Signal Quality
    </div>

    {_mrow("RSSI  (avg over all clients)",
           f'<span class="{_rssi_cls(rssi_dbm)}">{_cv(rssi_dbm, 1, " dBm")}</span>'
           f'&nbsp;<span class="badge {"b-g" if rssi_dbm and rssi_dbm >= -65 else "b-y" if rssi_dbm and rssi_dbm >= -78 else "b-r"}">'
           f'{"Good" if rssi_dbm and rssi_dbm >= -65 else "Weak" if rssi_dbm and rssi_dbm >= -78 else "Critical"}</span>')}

    {_mrow("Noise Floor",
           f'<span class="{_noise_cls(noise_dbm)}">{_cv(noise_dbm, 1, " dBm")}</span>'
           f'&nbsp;<span class="badge {"b-g" if noise_dbm and noise_dbm < -90 else "b-y" if noise_dbm and noise_dbm < -80 else "b-r"}">'
           f'{"Clean" if noise_dbm and noise_dbm < -90 else "Elevated" if noise_dbm and noise_dbm < -80 else "High"}</span>')}

    <div class="fbox">
      <strong>SNR = RSSI &minus; Noise Floor</strong>
      &nbsp;&nbsp;=&nbsp;&nbsp; {snr_formula}
    </div>

    {_mrow("SNR",
           f'<span class="{_snr_cls(snr_db)}">{_cv(snr_db, 1, " dB")}</span>'
           f'&nbsp;<span class="{snr_badge_cls} badge">{snr_label}</span>')}

    <div style="margin-top:0.45rem;font-size:0.76rem;color:#64748B;display:flex;gap:0.35rem;flex-wrap:wrap;">
      SNR quality bands: &nbsp;
      <span class="badge b-g">&gt; 25 dB &rarr; Excellent</span>
      <span class="badge b-g">20&ndash;25 dB &rarr; Good</span>
      <span class="badge b-y">10&ndash;20 dB &rarr; Moderate</span>
      <span class="badge b-r">&lt; 10 dB &rarr; Poor</span>
    </div>
  </div>

  {_arrow("SNR determines modulation, retry rate, and throughput")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ④ — Network Impact                  -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-net">
    <div class="cc-sec-title" style="color:#D97706;">
      ④ &nbsp; 🔁 &nbsp; Network Impact
    </div>

    {_mrow("Retry Rate",
           f'<span class="{_retry_cls(retry_pct)}">{_cv(retry_pct, 1, " %")}</span>'
           f'&nbsp;<span class="badge {"b-g" if retry_pct and retry_pct < 10 else "b-y" if retry_pct and retry_pct < 20 else "b-r"}">'
           f'{"Healthy" if retry_pct and retry_pct < 10 else "Warning" if retry_pct and retry_pct < 20 else "Critical"}</span>')}

    {_mrow("Packet Loss  (estimated, ≈ 70 % of retries → unique drops)",
           f'<span class="mv mv-y">{_cv(pkt_loss_pct, 1, " %")}</span>')}

    {_mrow("Modulation Efficiency  (derived from SNR)",
           f'<span class="{_snr_cls(snr_db)}">{mod_scheme}</span>')}

    {_mrow("Airtime Utilization  (spectrum occupancy)",
           f'<span class="{_airtime_cls(airtime_pct)}">{_cv(airtime_pct, 1, " %")}</span>')}

    {_mrow("Retransmission Airtime Overhead",
           f'<span class="mv mv-y">'
           f'≈ {_cv(retry_pct, 1, " %")} of channel capacity wasted on retries'
           f'</span>')}

    <div class="fbox">
      Retry formula (simulator):
      combined_retry = 1 &minus; (1 &minus; retry_SNR) &times; (1 &minus; retry_congestion)
      <br>
      retry_SNR = min(80%, 100% &times; e<sup>&minus;0.12 &times; SNR</sup>)
      &nbsp;&nbsp;&rarr;&nbsp;&nbsp; at SNR = {_cv(snr_db, 1, " dB")},
      retry_SNR &asymp; {_cv(min(80.0, max(1.0, 100.0 * math.exp(-0.12 * float(snr_db)))) if snr_db else None, 1, " %")}
    </div>
  </div>

  {_arrow("retransmissions and congestion reduce throughput and increase latency")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ⑤ — User Experience / QoE           -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-qoe">
    <div class="cc-sec-title" style="color:#DB2777;">
      ⑤ &nbsp; 👤 &nbsp; User Experience Impact  (QoE)
    </div>

    {_mrow("Estimated Throughput Degradation  (≈ 1.5× retry %)",
           f'<span class="mv mv-y">~{_cv(thput_deg_pct, 1, " %")}</span>')}

    {_mrow("Estimated Latency Increase  (≈ 1.2 ms per % retry)",
           f'<span class="mv mv-y">~{_cv(latency_ms, 0, " ms")}</span>')}

    {_mrow("QoE Score",
           f'<span class="{_qoe_cls(qoe_score)}">{_cv(qoe_score, 1, " / 100")}</span>')}

    {_mrow("QoE Category",
           f'<span class="{_qoe_cls(qoe_score)}">{qoe_cat}</span>')}

    <div class="fbox">
      QoE formula (simulator): &nbsp;
      QoE = 0.40 &times; SNR_score &nbsp;+&nbsp; 0.30 &times; Retry_score
            &nbsp;+&nbsp; 0.20 &times; Noise_score &nbsp;+&nbsp; 0.10 &times; Load_score
      <br>
      SNR_score = min(100, (SNR / 35) &times; 100) &nbsp;&nbsp;&rarr;&nbsp;&nbsp;
      {_cv(min(100, (snr_db / 35) * 100) if snr_db else None, 1)}
    </div>
  </div>

  {_arrow("QoE degradation triggers root cause analysis")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ⑥ — Root Cause Detection            -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-root">
    <div class="cc-sec-title" style="color:#DC2626;">
      ⑥ &nbsp; 🔍 &nbsp; Root Cause Detection
    </div>

    <div style="margin-bottom:0.6rem;">
      <span style="color:#64748B;font-size:0.83rem;font-weight:500;">Dominant Root Cause:</span>
      <br>
      <span class="rc-pill" style="margin-top:0.3rem;display:inline-block;">
        {root_cause_label}
      </span>
    </div>

    <div style="font-size:0.82rem;color:#64748B;margin-bottom:0.3rem;">
      Detection Confidence:
      <strong style="color:#0F172A;font-size:0.95rem;">&nbsp;{conf_pct}%</strong>
    </div>
    <div class="conf-track">
      <div class="conf-fill" style="width:{conf_pct}%;background:{conf_col};"></div>
    </div>

    <div style="margin-top:0.6rem;font-size:0.8rem;color:#64748B;">
      Root cause categories:
      &nbsp;<span class="badge b-r">Coverage Issue</span>
      &nbsp;<span class="badge b-r">Interference Issue</span>
      &nbsp;<span class="badge b-y">Congestion Issue</span>
      &nbsp;<span class="badge b-y">Capacity Issue</span>
      &nbsp;<span class="badge b-y">Obstruction Issue</span>
      &nbsp;<span class="badge b-g">System Optimal</span>
    </div>
  </div>

  {_arrow("root cause determines the optimal RRM action")}

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ⑦ — Recommendation Justification    -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-rec">
    <div class="cc-sec-title" style="color:#16A34A;">
      ⑦ &nbsp; ⚡ &nbsp; Recommendation Justification
    </div>

    {_mrow("Selected RRM Action",
           f'<span class="mv" style="color:#059669;font-size:0.95rem;font-weight:800;">{action}</span>')}

    {_mrow("Current Setting → Recommended Setting",
           f'<span class="mv">{cur_val}</span>'
           f'&nbsp;<span style="color:#64748B;">&rarr;</span>&nbsp;'
           f'<span class="mv mv-g">{rec_val}</span>')}

    {_mrow("Decision Confidence",
           f'<span class="mv mv-g">{int(confidence*100)} %</span>')}

    {_mrow("Expected QoE Gain",
           f'<span class="mv mv-g">+ {_cv(exp_gain, 1, " pts")}</span>')}

    <div class="jbox" style="text-align: left; font-family: sans-serif; white-space: pre-wrap; font-style: normal; color: #1E293B; background: #F8FAFC; border: 1px solid #CBD5E1; padding: 1rem; border-radius: 8px;">{justification}</div>
  </div>

  <!-- ══════════════════════════════════════════ -->
  <!-- LAYER ⑧ — Predicted Post-Action Impact    -->
  <!-- ══════════════════════════════════════════ -->
  <div class="cc-section cc-impact">
    <div class="cc-sec-title" style="color:#059669;">
      ⑧ &nbsp; 📈 &nbsp; Predicted Impact  (if Recommendation Applied)
    </div>

    {impact_html}
  </div>

  </div><!-- /cc-body -->
</div><!-- /cc-wrap -->
"""
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Main Causal Chain Report - Native Streamlit (NEW)
# ─────────────────────────────────────────────────────────────────────────────
def render_causal_chain_report(latest_row: dict, top_rec: dict, ap_id: str):
    """
    Renders the professional NOC incident report using native Streamlit components.
    """
    distance_m   = latest_row.get("distance")
    max_dist_m   = latest_row.get("max_distance")
    wall_count   = latest_row.get("wall_count")
    wall_loss_db = latest_row.get("wall_loss")
    freq_mhz     = latest_row.get("freq_mhz")    or 5180.0
    tx_power_dbm = latest_row.get("tx_power")    or 20.0
    airtime_frac = latest_row.get("airtime_utilization")
    int_type     = latest_row.get("interference_type") or "None"
    client_count = latest_row.get("client_count")
    channel      = latest_row.get("channel")
    scenario_nm  = latest_row.get("scenario_name", "Unknown")

    rssi_dbm     = latest_row.get("rssi")
    noise_dbm    = latest_row.get("noise_floor")
    snr_db       = latest_row.get("snr")
    retry_frac   = latest_row.get("retry_rate")
    qoe_score    = latest_row.get("qoe_score")
    qoe_cat      = latest_row.get("qoe_category") or "—"

    action       = (top_rec.get("action")       or "NONE") if top_rec else "NONE"
    confidence   = (top_rec.get("confidence")   or 0.80)   if top_rec else 0.80
    exp_gain     = (top_rec.get("expected_qoe_gain") or 0) if top_rec else 0
    cur_val      = (top_rec.get("current_value")     or "—") if top_rec else "—"
    rec_val      = (top_rec.get("recommended_value") or "—") if top_rec else "—"
    
    path_loss_db = compute_path_loss(distance_m, freq_mhz, wall_loss_db)
    est_rx_pwr   = (round(tx_power_dbm - path_loss_db, 1) if path_loss_db is not None else None)
    snr_label, _ = get_snr_label(snr_db)
    mod_scheme   = get_modulation(snr_db)
    
    retry_pct    = round((retry_frac or 0) * 100, 1)
    airtime_pct  = round((airtime_frac or 0) * 100, 1)
    pkt_loss_pct = round(retry_pct * 0.70, 1)
    thput_deg_pct= round(retry_pct * 1.50, 1)
    latency_ms   = round(retry_pct * 1.20, 0)
    
    ranked_causes = derive_root_cause_ranked(rssi_dbm, snr_db, noise_dbm, retry_frac, airtime_frac, int_type, distance_m)
    dominant_cause = ranked_causes[0]
    
    impact = estimate_post_action_impact(action, rssi_dbm, snr_db, qoe_score, retry_frac)

    # SEC 0: Executive Summary
    st.subheader("SECTION 0: EXECUTIVE SUMMARY")
    if "Coverage" in dominant_cause["label"]:
        exec_summary = f"Excessive path loss reduced RSSI and SNR. This degradation increased retransmissions ({retry_pct}%) and reduced user QoE ({qoe_score:.1f}/100)."
    elif "Bluetooth" in dominant_cause["label"]:
        exec_summary = f"Intermittent Bluetooth interference increased retransmissions ({retry_pct}%) despite healthy average signal quality, reducing network efficiency and QoE ({qoe_score:.1f}/100)."
    elif "Microwave" in dominant_cause["label"]:
        exec_summary = f"Broadband microwave interference caused packet corruption and retry events ({retry_pct}%), leading to reduced throughput and QoE ({qoe_score:.1f}/100)."
    elif "Neighbor" in dominant_cause["label"] or "Co-Channel" in dominant_cause["label"]:
        exec_summary = f"Neighbor AP traffic increased co-channel contention and reduced available capacity, elevating retries ({retry_pct}%) and lowering QoE ({qoe_score:.1f}/100)."
    elif "Congestion" in dominant_cause["label"]:
        exec_summary = f"Heavy airtime utilization ({airtime_pct}%) increased contention and reduced network efficiency, leading to higher collision probabilities and lower QoE ({qoe_score:.1f}/100)."
    else:
        exec_summary = f"Performance metrics deviated from nominal baselines. This lowered SNR, increased retransmissions ({retry_pct}%), and reduced user QoE ({qoe_score:.1f}/100)."

    exec_summary += f" The diagnostic engine identified **{dominant_cause['label']}** as the dominant root cause with {int(dominant_cause['conf']*100)}% confidence and recommended **{action}** to mitigate the issue."
    st.markdown(f"*{exec_summary}*")
    
    st.markdown("#### Causal Chain Summary")
    if "Coverage" in dominant_cause["label"]:
        flow = f"Distance & Obstacles\n&darr;\nHigh Path Loss ({path_loss_db:.1f} dB)\n&darr;\nWeak Received Signal ({rssi_dbm:.1f} dBm)\n&darr;\nReduced SNR ({snr_db:.1f} dB)\n&darr;\nLower MCS\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nThroughput Loss\n&darr;\n{action} Recommended"
    elif "Bluetooth" in dominant_cause["label"]:
        flow = f"Bluetooth Activity\n&darr;\nBurst RF Interference\n&darr;\nFrame Collisions\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nReduced Efficiency\n&darr;\n{action} Recommended"
    elif "Microwave" in dominant_cause["label"]:
        flow = f"Microwave Emissions\n&darr;\nBroadband RF Noise\n&darr;\nPacket Corruption\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nThroughput Reduction\n&darr;\n{action} Recommended"
    elif "Neighbor" in dominant_cause["label"] or "Co-Channel" in dominant_cause["label"]:
        flow = f"Neighbor AP Activity\n&darr;\nCo-channel Contention\n&darr;\nAirtime Competition\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nReduced Capacity\n&darr;\n{action} Recommended"
    elif "Congestion" in dominant_cause["label"]:
        flow = f"High Client Density\n&darr;\nAirtime Saturation ({airtime_pct}%)\n&darr;\nChannel Contention\n&darr;\nCollision Probability\n&darr;\nBackoff Delays\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nLatency Increase & QoE Reduction\n&darr;\n{action} Recommended"
    else:
        flow = f"Optimal Environmental Conditions\n&darr;\nHealthy Signal Quality\n&darr;\nNominal Retransmissions\n&darr;\nStrong User QoE ({qoe_score:.1f}/100)\n&darr;\nNo Action Required"
    
    st.markdown(f"<div style='text-align: center; font-weight: bold; color: #334155; line-height: 1.8; margin-bottom: 1rem;'>{flow.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
    st.divider()

    # SEC 1: Environment Analysis
    st.subheader("SECTION 1: ENVIRONMENT ANALYSIS")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Distance", f"{distance_m:.1f} m" if distance_m else "—")
    c2.metric("Walls", f"{wall_count}" if wall_count is not None else "—")
    c3.metric("Interference", int_type if int_type and int_type != "None" else "None")
    c4.metric("Airtime Utilization", f"{airtime_pct}%")
    
    env_reasoning = f"The environment contains {client_count or 'some'} clients with an average distance of {distance_m:.1f} meters. "
    if wall_count:
        env_reasoning += f"There are {wall_count} walls contributing to signal attenuation. "
    else:
        env_reasoning += f"Wall attenuation is minimal. "
    if int_type and int_type != "None":
        env_reasoning += f"{int_type} interference is actively present in the environment. "
    if airtime_pct > 70:
        env_reasoning += "Channel utilization is severely elevated, limiting available airtime for data transmission."
    else:
        env_reasoning += "Channel utilization remains within acceptable bounds."
    st.markdown(env_reasoning)
    st.divider()

    # SEC 2: Propagation Analysis
    st.subheader("SECTION 2: PROPAGATION ANALYSIS")
    c1, c2, c3 = st.columns(3)
    c1.metric("Transmit Power", f"{tx_power_dbm:.0f} dBm")
    c2.metric("Path Loss", f"{path_loss_db:.1f} dB" if path_loss_db else "—")
    c3.metric("Estimated RSSI", f"{est_rx_pwr:.1f} dBm" if est_rx_pwr else "—")
    
    prop_reasoning = f"The signal originates at {tx_power_dbm:.0f} dBm. Over the distance of {distance_m:.1f} meters, Free Space Path Loss and obstacles contribute to {path_loss_db:.1f} dB of total signal attenuation. "
    if est_rx_pwr and est_rx_pwr >= -65:
        prop_reasoning += "The resulting signal level at the receiver is excellent, providing a solid foundation for high-speed modulation."
    elif est_rx_pwr and est_rx_pwr >= -78:
        prop_reasoning += "The resulting signal level is adequate, though margins are reduced against unexpected noise spikes."
    else:
        prop_reasoning += "The heavy signal attenuation results in a weak received signal, directly impacting communication reliability."
    st.markdown(prop_reasoning)
    st.divider()

    # SEC 3: RF Signal Quality
    st.subheader("SECTION 3: RF SIGNAL QUALITY")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSSI", f"{rssi_dbm:.1f} dBm" if rssi_dbm else "—")
    c2.metric("Noise Floor", f"{noise_dbm:.1f} dBm" if noise_dbm else "—")
    c3.metric("SNR", f"{snr_db:.1f} dB" if snr_db else "—")
    
    snr_class = "🔴 Poor" if snr_db and snr_db < 10 else "🟡 Moderate" if snr_db and snr_db < 20 else "🟢 Good" if snr_db and snr_db <= 25 else "🟢 Excellent"
    c4.metric("SNR Classification", snr_class)
    
    rf_reasoning = f"The measured Signal-to-Noise Ratio (SNR) is {snr_db:.1f} dB, derived from the {rssi_dbm:.1f} dBm signal strength against a noise floor of {noise_dbm:.1f} dBm. "
    if snr_db and snr_db >= 20:
        rf_reasoning += "This indicates a healthy RF link capable of sustaining high-order modulation schemes."
    else:
        rf_reasoning += "Because the SNR is degraded, the wireless link has insufficient margin to correctly decode complex modulation. The AP and clients must downshift to slower, more robust modulation rates."
    st.markdown(rf_reasoning)
    st.divider()

    # SEC 4: Network Impact
    st.subheader("SECTION 4: NETWORK IMPACT")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Retry Rate", f"{retry_pct}%")
    c2.metric("Packet Loss (Est)", f"{pkt_loss_pct}%")
    c3.metric("Airtime Overhed", f"~{retry_pct}%")
    c4.metric("Modulation Efficiency", mod_scheme)
    
    if "Bluetooth" in dominant_cause["label"] or "Microwave" in dominant_cause["label"]:
        net_reasoning = f"The RF link remains strong and supports high modulation rates. However, intermittent bursty interference is overlapping with Wi-Fi frames. This elevates the retransmission rate to {retry_pct}% and reduces overall channel efficiency despite the healthy average SNR."
    elif "Congestion" in dominant_cause["label"]:
        net_reasoning = f"The RF link is healthy, but extreme client density has saturated the airtime. High contention leads to frame collisions and backoff delays, causing a {retry_pct}% retransmission rate."
    elif snr_db and snr_db >= 25:
        net_reasoning = f"The RF link remains strong and supports high modulation rates. However, intermittent interference or contention-related frame collisions are reducing channel efficiency despite the healthy average SNR. The network currently experiences a {retry_pct}% retransmission rate."
    elif snr_db and snr_db >= 20:
        net_reasoning = f"The RF link is good, but retransmissions ({retry_pct}%) are consuming valuable airtime, mildly reducing overall channel efficiency."
    else:
        net_reasoning = f"As the SNR shifts to {snr_db:.1f} dB, frames become harder to decode correctly. The network currently experiences a {retry_pct}% retransmission rate. "
        net_reasoning += "These additional retransmissions consume valuable airtime, reducing overall channel efficiency and leaving less capacity for new data."
    st.markdown(net_reasoning)
    st.divider()

    # SEC 5: User Experience Impact
    st.subheader("SECTION 5: USER EXPERIENCE IMPACT")
    c1, c2, c3 = st.columns(3)
    c1.metric("Throughput Degradation", f"~{thput_deg_pct}%")
    c2.metric("Latency Increase", f"~{latency_ms} ms")
    c3.metric("QoE Score", f"{qoe_score:.1f} / 100" if qoe_score else "—")
    
    if qoe_score and qoe_score >= 85:
        qoe_reasoning = "User experience remains largely unaffected. The network easily compensates for any minor environmental factors."
    elif qoe_score and qoe_score >= 70:
        qoe_reasoning = "Users may notice moderate performance degradation. Retransmissions and delays are starting to impact responsiveness."
    else:
        qoe_reasoning = "Users are likely experiencing noticeable performance issues. Elevated retransmissions severely reduce usable throughput and increase latency."
    st.markdown(qoe_reasoning)
    st.divider()

    # SEC 6: Root Cause Analysis
    st.subheader("SECTION 6: ROOT CAUSE ANALYSIS")
    st.markdown(f"**Root Cause:** {dominant_cause['label']}")
    st.markdown(f"**Confidence:** {'High' if dominant_cause['conf'] >= 0.85 else 'Moderate' if dominant_cause['conf'] >= 0.6 else 'Low'}")
    
    st.markdown("**Supporting Evidence:**")
    for ev in dominant_cause['reason'].split(';'):
        st.markdown(f"- ✓ {ev.strip()}")
        
    if "Bluetooth" in dominant_cause['label']:
        st.markdown(f"- ✓ Bluetooth interference signature identified")
        st.markdown(f"- ✓ Retransmission rate elevated ({retry_pct}%)")
        st.markdown(f"- ✓ Average RSSI and SNR remain healthy")
    elif "Microwave" in dominant_cause['label']:
        st.markdown(f"- ✓ Broadband noise detected ({noise_dbm:.1f} dBm)")
        st.markdown(f"- ✓ Packet corruption rate increased ({retry_pct}%)")
    elif "Neighbor" in dominant_cause['label'] or "Co-Channel" in dominant_cause['label']:
        st.markdown(f"- ✓ Co-channel contention detected from Neighbor AP")
        st.markdown(f"- ✓ Increased airtime competition ({airtime_pct}%)")
    elif "Congestion" in dominant_cause['label']:
        st.markdown(f"- ✓ Airtime utilization extremely high ({airtime_pct}%)")
        st.markdown(f"- ✓ Channel saturation observed")
        st.markdown(f"- ✓ Excellent RF signal quality (SNR: {snr_db:.1f} dB)")
    elif "Coverage" in dominant_cause['label']:
        st.markdown(f"- ✓ RSSI degraded below -78 dBm ({rssi_dbm:.1f} dBm)")
        st.markdown(f"- ✓ Path loss significant ({path_loss_db:.1f} dB)")
        st.markdown(f"- ✓ Noise floor is clean ({noise_dbm:.1f} dBm)")
        st.markdown(f"- ✓ Airtime is nominal")
        
    st.markdown("**Alternative Causes Considered:**")
    for cause in ranked_causes[1:3]:
        st.markdown(f"*{cause['label']}*")
        if "Coverage" in cause['label']:
            st.markdown(f"  - ✗ RSSI is stronger than -65 dBm" if rssi_dbm >= -65 else f"  - ✗ RSSI is adequate ({rssi_dbm:.1f} dBm)")
            st.markdown(f"  - ✗ Excellent SNR ({snr_db:.1f} dB)" if snr_db >= 25 else "")
            st.markdown(f"  - ✗ Coverage symptoms absent")
        elif "Interference" in cause['label']:
            st.markdown(f"  - ✗ Noise floor is clean ({noise_dbm:.1f} dBm)" if noise_dbm < -90 else "  - ✗ Symptoms align better with primary cause")
        elif "Congestion" in cause['label']:
            st.markdown(f"  - ✗ Airtime utilization only {airtime_pct}%" if airtime_pct < 75 else "  - ✗ Symptoms align better with primary cause")
            st.markdown(f"  - ✗ Channel saturation not observed" if airtime_pct < 75 else "")
        else:
            st.markdown(f"  - ✗ Evidence does not strongly support this cause")
            
    st.divider()

    # SEC 7: Recommendation Justification
    st.subheader("SECTION 7: RECOMMENDATION JUSTIFICATION")
    st.markdown(f"**Selected Action:** `{action}`")
    rec_justification = f"The action **{action}** was selected directly in response to the diagnosed {dominant_cause['label']}. "
    if action == "CHANNEL_CHANGE":
        if "Bluetooth" in dominant_cause['label']:
            rec_justification += "Although the measured SNR remains in the excellent range, Bluetooth interference introduces intermittent bursts of non-WiFi interference. These bursts increase retransmissions and reduce channel efficiency despite otherwise healthy signal conditions. CHANNEL_CHANGE is therefore a preventative optimization designed to improve reliability and reduce future interference-related retransmissions."
        elif "Microwave" in dominant_cause['label']:
            rec_justification += "Microwave emissions raise noise across portions of the 2.4 GHz spectrum. CHANNEL_CHANGE avoids this broadband interference, stopping the packet corruption and recovering throughput."
        else:
            rec_justification += "Migrating to a cleaner channel will evade the active interference, lowering the noise floor and restoring the SNR margin required for high throughput."
    elif action == "LOAD_BALANCE":
        if "Neighbor" in dominant_cause['label'] or "Co-Channel" in dominant_cause['label']:
            rec_justification += "Neighbor AP traffic increases contention. The recommendation is LOAD_BALANCE because contention is causing airtime competition, not noise. Distributing clients will alleviate this co-channel pressure."
        else:
            rec_justification += "Steering clients to adjacent APs will alleviate localized congestion, bringing airtime utilization back to manageable levels."
    elif action == "POWER_INCREASE":
        rec_justification += "Increasing AP transmit power compensates for the excessive path loss, raising the RSSI at the client end and recovering link stability."
    elif action == "WIDTH_ADJUST":
        rec_justification += "Narrowing the channel width reduces the noise footprint and limits exposure to channel contention, granting better efficiency which is critical in dense deployments."
    elif action == "POWER_DECREASE":
        rec_justification += "Reducing TX power shrinks the cell boundary, curtailing co-channel overlap and improving overall spectral reuse."
    else:
        rec_justification += "No intrusive changes are recommended as the system is operating near optimal bounds."
    st.markdown(rec_justification)
    st.divider()

    # SEC 8: Predicted Improvement
    st.subheader("SECTION 8: PREDICTED IMPROVEMENT")
    st.markdown("*(Based on simulator models and current network conditions)*")
    if action == "NONE":
        st.info("System is operating optimally. No metric changes predicted.")
    else:
        df_impact = pd.DataFrame([
            {"Metric": "RSSI", "Current": f"{impact['rssi_before']:.1f} dBm", "Predicted": f"{impact['rssi_after']:.1f} dBm", "Change": f"{impact['rssi_after'] - impact['rssi_before']:+.1f} dB"},
            {"Metric": "SNR", "Current": f"{impact['snr_before']:.1f} dB", "Predicted": f"{impact['snr_after']:.1f} dB", "Change": f"{impact['snr_after'] - impact['snr_before']:+.1f} dB"},
            {"Metric": "Retry Rate", "Current": f"{impact['retry_before']*100:.1f}%", "Predicted": f"{impact['retry_after']*100:.1f}%", "Change": f"{(impact['retry_after'] - impact['retry_before'])*100:+.1f}%"},
            {"Metric": "QoE Score", "Current": f"{impact['qoe_before']:.1f}/100", "Predicted": f"{impact['qoe_after']:.1f}/100", "Change": f"{impact['qoe_after'] - impact['qoe_before']:+.1f}"}
        ])
        st.dataframe(df_impact, hide_index=True, use_container_width=True)
        
        if action == "POWER_INCREASE":
            imp_expl = f"By increasing transmit power, RSSI improves by {impact['rssi_after'] - impact['rssi_before']:.1f} dB, recovering the lost SNR margin and virtually eliminating coverage-based retries."
        elif action == "CHANNEL_CHANGE":
            imp_expl = f"Moving to a clean channel avoids the bursty RF interference, reducing the retry rate by {(impact['retry_before'] - impact['retry_after'])*100:.1f}% and recovering the user QoE."
        elif action == "LOAD_BALANCE" or action == "WIDTH_ADJUST":
            imp_expl = f"By redistributing the load and minimizing contention, the airtime competition drops significantly. This directly resolves the frame collisions, reducing the retry rate by {(impact['retry_before'] - impact['retry_after'])*100:.1f}%."
        else:
            imp_expl = "The recommended action adjusts RRM parameters to stabilize the link, improving overall network efficiency."
        
        st.markdown(f"<br>**Why this improves performance:** {imp_expl}", unsafe_allow_html=True)

    st.divider()

    # Technical Reference (Engineering Details)
    with st.expander("Technical Reference (Engineering Details)"):
        st.markdown("""
        ### Path Loss Model
        **Formula:** `Path Loss = 32.44 + 20log10(f_MHz) + 20log10(d_km) + (Wall_Count * 3.0)`
        - **Current Values:** Frequency = {freq} MHz, Distance = {dist} km, Wall Loss = {wl} dB
        - **Result:** {pl} dB
        - **Source:** Log-Distance Indoor Path Loss Model.
        - **Reason:** Used to estimate signal attenuation over distance and through walls.
        
        ### SNR (Signal-to-Noise Ratio)
        **Formula:** `SNR = RSSI - Noise Floor`
        - **Current Values:** RSSI = {rssi} dBm, Noise Floor = {nf} dBm
        - **Result:** {snr} dB
        - **Source:** Standard RF engineering definition (IEEE 802.11).
        - **Reason:** Measures available signal margin above background RF noise.
        
        ### Retry Model
        **Formula:** `Retry = 1 - (1 - Retry_SNR)(1 - Retry_Congestion)`
        - **Current Values:** SNR = {snr} dB, Congestion = {airtime}%
        - **Result:** {retry}%
        - **Source:** Engineering heuristic representing RF corruption and contention effects.
        - **Reason:** Models retransmissions caused by both poor RF quality and channel contention.
        """.format(
            freq=freq_mhz,
            dist=round((distance_m or 1.0)/1000.0, 4),
            wl=wall_loss_db or 0,
            pl=path_loss_db,
            rssi=rssi_dbm,
            nf=noise_dbm,
            snr=snr_db,
            airtime=airtime_pct,
            retry=retry_pct
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Plain-Text Report Builder (for download / copy)
# ─────────────────────────────────────────────────────────────────────────────
def build_plain_text_report(latest_row: dict, top_rec: dict, ap_id: str) -> str:
    distance_m   = latest_row.get("distance")
    max_dist_m   = latest_row.get("max_distance")
    wall_count   = latest_row.get("wall_count")
    wall_loss_db = latest_row.get("wall_loss")
    freq_mhz     = latest_row.get("freq_mhz")    or 5180.0
    tx_power_dbm = latest_row.get("tx_power")    or 20.0
    airtime_frac = latest_row.get("airtime_utilization")
    int_type     = latest_row.get("interference_type") or "None"
    client_count = latest_row.get("client_count")
    scenario_nm  = latest_row.get("scenario_name", "Unknown")

    rssi_dbm     = latest_row.get("rssi")
    noise_dbm    = latest_row.get("noise_floor")
    snr_db       = latest_row.get("snr")
    retry_frac   = latest_row.get("retry_rate")
    qoe_score    = latest_row.get("qoe_score")
    qoe_cat      = latest_row.get("qoe_category") or "—"

    action      = (top_rec.get("action")       or "NONE") if top_rec else "NONE"
    confidence  = (top_rec.get("confidence")   or 0.80)   if top_rec else 0.80
    rc_from_rec = (top_rec.get("root_cause")   or "")     if top_rec else ""
    exp_gain    = (top_rec.get("expected_qoe_gain") or 0) if top_rec else 0
    cur_val     = (top_rec.get("current_value")     or "—") if top_rec else "—"
    rec_val     = (top_rec.get("recommended_value") or "—") if top_rec else "—"

    path_loss_db  = compute_path_loss(distance_m, freq_mhz, wall_loss_db)
    est_rx_pwr    = (round(tx_power_dbm - path_loss_db, 1)
                     if path_loss_db is not None else None)

    if rc_from_rec and rc_from_rec not in ("NONE", "None", ""):
        root_cause_label = rc_from_rec.replace("_", " ").title()
        root_conf = confidence
    else:
        root_cause_label, root_conf = derive_root_cause(
            rssi_dbm, snr_db, noise_dbm, retry_frac, airtime_frac, int_type, distance_m
        )

    snr_label_txt, _ = get_snr_label(snr_db)
    mod_scheme        = get_modulation(snr_db)
    just              = build_justification_text(
        action, rssi_dbm, snr_db, noise_dbm, distance_m,
        wall_count, retry_frac, qoe_score, int_type, airtime_frac
    )
    impact = estimate_post_action_impact(action, rssi_dbm, snr_db, qoe_score, retry_frac)

    def v(x, d=1, s=""): return f"{round(float(x),d)}{s}" if x is not None else "—"
    def vp(x, d=1): return v(float(x)*100, d, " %") if x is not None else "—"

    lines = [
        "═" * 65,
        "  EXPLAIN CAUSAL METRIC CHAIN — ENGINEERING REPORT",
        f"  AP: {ap_id}    Scenario: {scenario_nm}",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "═" * 65,
        "",
        "━" * 40,
        " [1] ENVIRONMENT FACTORS",
        "━" * 40,
        f"  Client Distance (avg)        : {v(distance_m, 1, ' m')}",
        f"  Client Distance (max)        : {v(max_dist_m, 1, ' m')}",
        f"  Walls / Obstacles            : {wall_count or '—'} wall(s)  → {v(wall_loss_db, 1, ' dB')} attenuation",
        f"  Interference Source          : {int_type}",
        f"  Channel Utilization          : {vp(airtime_frac)}",
        f"  Connected Clients            : {client_count or '—'}",
        f"  Frequency / TX Power         : {v(freq_mhz, 0, ' MHz')} / {v(tx_power_dbm, 0, ' dBm')}",
        "",
        "━" * 40,
        " [2] PROPAGATION ANALYSIS",
        "━" * 40,
        "  Path Loss Model              : Log-Distance Indoor (n = 3.0)",
        f"  Computed Path Loss           : {v(path_loss_db, 1, ' dB')}",
        f"  Wall Attenuation             : {v(wall_loss_db, 1, ' dB')}  ({wall_count or 0} × 3.0 dB/wall)",
        f"  Estimated Received Power     : {v(est_rx_pwr, 1, ' dBm')}  (TX − PL)",
        "",
        "━" * 40,
        " [3] RF SIGNAL QUALITY",
        "━" * 40,
        f"  RSSI                         : {v(rssi_dbm, 1, ' dBm')}",
        f"  Noise Floor                  : {v(noise_dbm, 1, ' dBm')}",
        f"  SNR = RSSI − Noise Floor     : {v(rssi_dbm, 1, ' dBm')} − ({v(noise_dbm, 1, ' dBm')}) = {v(snr_db, 1, ' dB')}",
        f"  SNR Quality Tier             : {snr_label_txt}",
        "",
        "━" * 40,
        " [4] NETWORK IMPACT",
        "━" * 40,
        f"  Retry Rate                   : {vp(retry_frac)}",
        f"  Packet Loss (est.)           : {v((retry_frac or 0)*70, 1, ' %')}",
        f"  Modulation Scheme            : {mod_scheme}",
        f"  Airtime Utilization          : {vp(airtime_frac)}",
        "",
        "━" * 40,
        " [5] USER EXPERIENCE IMPACT",
        "━" * 40,
        f"  Throughput Degradation (est.): ~{v((retry_frac or 0)*100*1.5, 1, ' %')}",
        f"  Latency Increase (est.)      : ~{v((retry_frac or 0)*100*1.2, 0, ' ms')}",
        f"  QoE Score                    : {v(qoe_score, 1, ' / 100')}  ({qoe_cat})",
        "",
        "━" * 40,
        " [6] ROOT CAUSE DETECTION",
        "━" * 40,
        f"  Dominant Root Cause          : {root_cause_label}",
        f"  Confidence Score             : {int(root_conf*100)} %",
        "",
        "━" * 40,
        " [7] RECOMMENDATION JUSTIFICATION",
        "━" * 40,
        f"  Action                       : {action}",
        f"  Current Setting              : {cur_val}",
        f"  Recommended Setting          : {rec_val}",
        f"  Decision Confidence          : {int(confidence*100)} %",
        f"  Expected QoE Gain            : + {v(exp_gain, 1, ' pts')}",
        "",
        "  Justification:",
        "",
        f"  {just}",
        "",
        "━" * 40,
        " [8] PREDICTED IMPACT (if recommendation applied)",
        "━" * 40,
        f"  RSSI     : {v(impact['rssi_before'], 1, ' dBm')}  →  {v(impact['rssi_after'], 1, ' dBm')}",
        f"  SNR      : {v(impact['snr_before'], 1, ' dB')}  →  {v(impact['snr_after'], 1, ' dB')}",
        f"  QoE      : {v(impact['qoe_before'], 1, ' / 100')}  →  {v(impact['qoe_after'], 1, ' / 100')}",
        f"  Retry    : {vp(impact['retry_before'])}  →  {vp(impact['retry_after'])}",
        "",
        "═" * 65,
        "  End of Report",
        "═" * 65,
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Page Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="pg-header">📶 &nbsp; Client-Aware WiFi Digital Twin</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pg-sub">Live Physical Network Simulation &amp; Explainable RRM Decisions</div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/wifi.png", width=60)
st.sidebar.markdown("### Controls & Actions")

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()

if st.sidebar.button("⚡ Trigger Simulation Step", use_container_width=True):
    if trigger_simulator_step():
        st.sidebar.success("Simulation step triggered!")
        st.rerun()
    else:
        st.sidebar.error("Could not reach simulator. Is the backend running?")

st.sidebar.markdown("---")
st.sidebar.markdown("### Manual Scenario Control")

ap_summaries = fetch_from_api("/ap-status")
selected_ap  = None

if ap_summaries:
    ap_ids      = [ap["ap_id"] for ap in ap_summaries]
    selected_ap = st.selectbox("Select Access Point:", ap_ids)

    SCENARIOS = [
        "Normal Office",
        "Bluetooth Storm",
        "Microwave Burst",
        "Neighbor AP Congestion",
        "Crowded Conference Room",
        "Weak Signal Corner",
    ]
    force_scen = st.sidebar.selectbox("Force Scenario:", SCENARIOS)
    if st.sidebar.button("▶ Apply Scenario", use_container_width=True):
        set_scenario(selected_ap, force_scen)
        st.sidebar.success(f"✅ Forced: {force_scen}")
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# AP Health Scorecard Row
# ─────────────────────────────────────────────────────────────────────────────
if ap_summaries:
    st.markdown("### 🖥️ Access Point Status Scorecard")
    cols = st.columns(max(1, len(ap_summaries)))
    for idx, ap in enumerate(ap_summaries):
        with cols[idx]:
            cls, icon = "hcard-ok", "🟢"
            if ap["status"] == "Warning":
                cls, icon = "hcard-warn", "🟡"
            elif ap["status"] == "Critical":
                cls, icon = "hcard-crit", "🔴"
            st.markdown(f"""
            <div class="hcard {cls}">
              <div class="hcard-title">{icon} {ap['ap_id']}</div>
              <div style="margin-top:0.4rem;line-height:1.7;">
                <span class="mlabel">Status:</span> <b>{ap['status']}</b><br/>
                <span class="mlabel">Clients:</span> <b>{ap['client_count']}</b><br/>
                <span class="mlabel">Alerts:</span> <b>{ap['active_alert_count']}</b><br/>
                <span class="mlabel">Last Action:</span>
                <code style="font-size:0.73rem;">{ap['recent_recommendation']}</code>
              </div>
            </div>""", unsafe_allow_html=True)
else:
    st.warning("⚠️  No Access Point data. Start the FastAPI backend first (`python run.py`).")

# ─────────────────────────────────────────────────────────────────────────────
# Main content — requires a selected AP
# ─────────────────────────────────────────────────────────────────────────────
if ap_summaries and selected_ap:

    # Scenario Event Timeline
    st.markdown("### 📋 Scenario Event Timeline")
    history = fetch_from_api("/scenario/history", params={"ap_id": selected_ap, "limit": 5})
    if history:
        parts = []
        for h in reversed(history):
            t_str   = pd.to_datetime(h["start_time"]).strftime("%H:%M")
            segment = f"**{t_str} — {h['scenario_name']}**"
            if h.get("recommendation_triggered"):
                segment += f" &rarr; `{h['recommendation_triggered']}`"
            parts.append(segment)
        st.markdown("  |  ".join(parts))
    else:
        st.caption("No scenario history yet.")

    # ── Fetch data ─────────────────────────────────────────────────────────
    telemetry_data = fetch_from_api("/telemetry",       params={"ap_id": selected_ap, "limit": 100})
    recs           = fetch_from_api("/recommendations", params={"limit": 5, "ap_id": selected_ap})
    alerts         = fetch_from_api("/alerts",          params={"limit": 50, "ap_id": selected_ap})

    if not telemetry_data:
        st.info("ℹ️  No telemetry data yet. Trigger a simulation step or wait for the auto-loop.")
    else:
        df = pd.DataFrame(telemetry_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        latest_row = df.iloc[-1].to_dict()
        top_rec    = recs[0] if recs else None

        # ── TAB LAYOUT ──────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯  Root Cause & Topology",
            "🔗  Explain Causal Metric Chain",
            "📊  Physics Telemetry",
            "🔔  Recommendations & Alerts",
        ])

        # ════════════════════════════════════════════════════════════════════
        # TAB 1 — Root Cause & Topology
        # ════════════════════════════════════════════════════════════════════
        with tab1:
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("#### Explainability Panel")
                st.markdown('<div class="explain-panel">', unsafe_allow_html=True)

                if top_rec:
                    eg = top_rec.get("expected_qoe_gain", 0.0)
                    st.markdown(f"**Current Scenario:** {latest_row.get('scenario_name', 'Unknown')}")
                    st.markdown(f"**Root Cause:** `{top_rec.get('root_cause', 'NONE')}`")
                    st.markdown("---")
                    st.markdown("**Causal Metric Chain (backend reason field):**")
                    for line in top_rec.get("reason", "").split("\n"):
                        if ":" in line:
                            st.markdown(f"- {line.strip()}")
                    st.markdown("---")
                    st.markdown(
                        f"**Action:** `{top_rec['action']}`  "
                        f"(Confidence: {top_rec['confidence']*100:.1f}%)"
                    )
                    qoe_now = latest_row.get("qoe_score", 0.0) or 0.0
                    st.markdown(
                        f"**Expected QoE after action:** "
                        f"{min(100.0, qoe_now + eg):.1f} (+{eg:.1f})"
                    )
                else:
                    st.info("No recommendation data yet.")

                st.markdown("</div>", unsafe_allow_html=True)

                explain_causal = st.checkbox("Explain Causal Metric Chain", value=False, key="explain_causal_tab1")
                if explain_causal:
                    if top_rec:
                        st.markdown("---")
                        st.markdown("##### 🔗 Causal Metric Chain Report")
                        render_causal_chain_report(latest_row, top_rec, selected_ap)
                    else:
                        st.warning("No recommendation record found to explain.")

                # ── Explain button hint ──────────────────────────────────
                st.markdown("")
                st.markdown(
                    '<div class="explain-hint">🔗 &nbsp; See full causal chain → '
                    'open the <em>"Explain Causal Metric Chain"</em> tab above</div>',
                    unsafe_allow_html=True
                )

            with col_right:
                st.markdown("#### Live Client Topology")
                if history and history[0].get("client_topology_snapshot"):
                    try:
                        topology = json.loads(history[0]["client_topology_snapshot"])
                        if topology:
                            df_top = pd.DataFrame(topology)
                            import plotly.express as px
                            import plotly.graph_objects as go
                            fig = px.scatter(
                                df_top, x="x", y="y", text="id",
                                title="Client Floor-Plan", range_x=[0, 50], range_y=[0, 50],
                                labels={"x": "X (m)", "y": "Y (m)"},
                            )
                            fig.update_traces(marker=dict(size=10, color="#3B82F6"), textposition="top center")
                            fig.add_scatter(
                                x=[df_top["x"].mean()], y=[df_top["y"].mean()],
                                mode="markers+text", text=["AP"],
                                marker=dict(size=20, color="#EF4444", symbol="star"),
                                textposition="top center",
                                name="Access Point",
                            )
                            fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=32, b=0))
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No client positions in topology snapshot.")
                    except Exception:
                        st.info("Error parsing topology snapshot.")
                else:
                    st.info("Topology snapshot not available yet.")

        # ════════════════════════════════════════════════════════════════════
        # TAB 2 — EXPLAIN CAUSAL METRIC CHAIN  ← THE MAIN FEATURE
        # ════════════════════════════════════════════════════════════════════
        with tab2:
            # Header + description
            st.markdown("#### 🔗 Explain Causal Metric Chain")
            st.markdown(
                """
                > **How to read this report:** Each layer in the chain is causally linked to the next.
                > Follow the arrows ↓ from physical environment conditions all the way through
                > to the final recommendation, with every numerical value sourced from live telemetry.
                > Color coding: 🟢 **Green** = Healthy &nbsp;|&nbsp; 🟡 **Yellow** = Warning &nbsp;|&nbsp; 🔴 **Red** = Critical
                """
            )

            if not top_rec:
                st.warning(
                    "⚠️  No recommendation record found for this AP yet. "
                    "Trigger a simulation step to generate recommendations."
                )
            else:
                # Quick KPI strip above the report
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("RSSI",        f"{latest_row.get('rssi', 0):.1f} dBm")
                k2.metric("Noise Floor", f"{latest_row.get('noise_floor', 0):.1f} dBm")
                k3.metric("SNR",         f"{latest_row.get('snr', 0):.1f} dB")
                k4.metric("Retry Rate",  f"{latest_row.get('retry_rate', 0)*100:.1f} %")
                k5.metric("Airtime",     f"{latest_row.get('airtime_utilization', 0)*100:.1f} %")
                k6.metric("QoE",         f"{latest_row.get('qoe_score', 0):.1f} / 100")

                st.markdown("---")

                # ── FULL CAUSAL CHAIN REPORT ─────────────────────────────
                render_causal_chain_report(latest_row, top_rec, selected_ap)

                st.markdown("---")

                # ── DOWNLOAD BUTTON (acts as "Copy Explanation") ─────────
                plain_text = build_plain_text_report(latest_row, top_rec, selected_ap)
                fname = (f"causal_chain_{selected_ap}_"
                         f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

                dl_col, _ = st.columns([1, 2])
                with dl_col:
                    st.download_button(
                        label="📋  Copy / Download Explanation",
                        data=plain_text,
                        file_name=fname,
                        mime="text/plain",
                        help="Downloads the full causal chain as a plain-text file you can copy and share.",
                        use_container_width=True,
                    )

        # ════════════════════════════════════════════════════════════════════
        # TAB 3 — Physics Telemetry (unchanged from original)
        # ════════════════════════════════════════════════════════════════════
        with tab3:
            st.markdown("#### Physical Environment Summary")
            p1, p2, p3, p4, p5 = st.columns(5)
            dist_v = latest_row.get("distance", 0) or 0
            mxd_v  = latest_row.get("max_distance", 0) or 0
            wc_v   = latest_row.get("wall_count", 0)   or 0
            wl_v   = latest_row.get("wall_loss", 0)    or 0
            fr_v   = latest_row.get("freq_mhz", 0)     or 0
            tx_v   = latest_row.get("tx_power", 0)     or 0
            it_v   = latest_row.get("interference_type", "None") or "None"
            p1.metric("Distance (avg / max)",    f"{dist_v:.1f} m / {mxd_v:.1f} m")
            p2.metric("Wall Count (loss)",       f"{wc_v}  ({wl_v:.1f} dB)")
            p3.metric("Frequency",               f"{fr_v:.0f} MHz")
            p4.metric("TX Power",                f"{tx_v:.0f} dBm")
            p5.metric("Interference",            it_v)

            st.markdown("---")
            st.markdown("#### Causal Chain Over Time")
            ch1, ch2 = st.columns(2)

            with ch1:
                st.markdown("**1 · Client Distance (m)**")
                if "distance" in df.columns:
                    st.line_chart(df["distance"])
                st.markdown("**2 · Signal Quality — RSSI, SNR & Noise Floor**")
                st.line_chart(df[["rssi", "snr", "noise_floor"]])
                st.markdown("**3 · Packet Retry Rate**")
                st.line_chart(df["retry_rate"])

            with ch2:
                st.markdown("**4 · QoE Score**")
                if "qoe_score" in df.columns:
                    st.line_chart(df["qoe_score"])
                st.markdown("**5 · Airtime Spectrum Occupancy**")
                st.line_chart(df["airtime_utilization"])
                st.markdown("**6 · Connected Client Density**")
                st.bar_chart(df["client_count"])

        # ════════════════════════════════════════════════════════════════════
        # TAB 4 — Recommendations & Alerts (unchanged from original)
        # ════════════════════════════════════════════════════════════════════
        with tab4:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### Ranked RRM Recommendations")
                if recs:
                    df_recs = pd.DataFrame(recs)
                    df_recs["timestamp"] = pd.to_datetime(df_recs["timestamp"])
                    show_cols = ["timestamp", "action", "confidence", "root_cause"]
                    if "expected_qoe_gain" in df_recs.columns:
                        show_cols.insert(3, "expected_qoe_gain")
                    st.dataframe(df_recs[show_cols], hide_index=True, use_container_width=True)
                else:
                    st.info("No recommendations yet.")

            with col_b:
                st.markdown("#### Scenario-Aware Alerts")
                if alerts:
                    df_alerts = pd.DataFrame(alerts)
                    df_alerts["timestamp"] = pd.to_datetime(df_alerts["timestamp"])
                    for _, alert in df_alerts.head(5).iterrows():
                        sev_icon = "🔴" if "interference" in str(alert.get("alert_type", "")) else "🟡"
                        st.markdown(
                            f"**{sev_icon} {str(alert['alert_type']).replace('_', ' ').title()}**"
                        )
                        st.caption(str(alert.get("description", "")))
                        st.markdown("---")
                else:
                    st.success("✅ No active anomalies detected.")
