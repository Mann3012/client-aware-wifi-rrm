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

from dashboard.causal_chain import (
    build_justification_text,
    derive_root_cause,
    derive_root_cause_ranked,
    estimate_post_action_impact,
    format_root_cause_label,
    get_modulation,
    get_snr_label,
    interference_matches,
    normalize_interference_label,
    parse_spectrum_snapshot,
)

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
    if v >= 85:   return "mv mv-g"
    if v >= 65:   return "mv mv-y"
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
    return ""


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
    rc_from_rec  = (top_rec.get("root_cause")   or "")     if top_rec else ""
    rec_reason   = (top_rec.get("reason")        or "")    if top_rec else ""

    path_loss_db = None
    est_rx_pwr   = None
    snr_label, _ = get_snr_label(snr_db)
    mod_scheme   = get_modulation(snr_db)

    retry_pct    = round((retry_frac or 0) * 100, 1)
    airtime_pct  = round((airtime_frac or 0) * 100, 1)
    pkt_loss_pct = round(retry_pct * 0.70, 1)
    thput_deg_pct= round(retry_pct * 1.50, 1)
    latency_ms   = round(retry_pct * 1.20, 0)

    spectrum = parse_spectrum_snapshot(latest_row.get("spectrum_snapshot"))

    ranked_causes = derive_root_cause_ranked(
        rssi_dbm, snr_db, noise_dbm, retry_frac, airtime_frac, int_type, distance_m,
        rec_root_cause=rc_from_rec,
    )
    dominant_cause = ranked_causes[0]
    if rc_from_rec and rc_from_rec not in ("NONE", "None", ""):
        dominant_cause = {**dominant_cause, "conf": max(dominant_cause["conf"], confidence)}

    # Removed estimate_post_action_impact

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
    c3.metric("Interference", normalize_interference_label(int_type))
    c4.metric("Airtime Utilization", f"{airtime_pct}%")

    if spectrum:
        st.markdown("#### Sensing Radio — Spectrum Snapshot")
        sc1, sc2, sc3, sc4 = st.columns(4)
        spec = spectrum.get("spectrum", {})
        sc1.metric("Channel Quality", f"{spectrum.get('channel_quality_score', '—')}/100")
        sc2.metric("Spectrum Noise Floor", f"{spec.get('noise_floor_dbm', '—')} dBm")
        sc3.metric("Peak Power", f"{spec.get('peak_power_dbm', '—')} dBm")
        sc4.metric("Channel Busy", f"{(spec.get('channel_busy_fraction', 0) or 0) * 100:.1f}%")
        interferers = spectrum.get("detected_interferers") or []
        if interferers:
            st.markdown("**Detected Interferers (Sensing Radio):**")
            for inf in interferers[:5]:
                st.markdown(
                    f"- `{inf.get('classification', 'unknown')}` @ {inf.get('center_freq_mhz', '—')} MHz "
                    f"({inf.get('power_dbm', '—')} dBm, duty {((inf.get('duty_cycle') or 0) * 100):.0f}%)"
                )
    
    env_reasoning = f"The environment contains {client_count or 'some'} clients with an average distance of {distance_m:.1f} meters. "
    if wall_count:
        env_reasoning += f"There are {wall_count} walls contributing to signal attenuation. "
    else:
        env_reasoning += f"Wall attenuation is minimal. "
    if int_type and int_type != "None":
        env_reasoning += f"{normalize_interference_label(int_type)} interference is actively present in the environment. "
    if airtime_pct > 70:
        env_reasoning += "Channel utilization is severely elevated, limiting available airtime for data transmission."
    else:
        env_reasoning += "Channel utilization remains within acceptable bounds."
    st.markdown(env_reasoning)
    st.divider()

    # SEC 2: Propagation Analysis
    st.subheader("SECTION 2: PROPAGATION ANALYSIS")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transmit Power", f"{tx_power_dbm:.0f} dBm")
    c2.metric("Path Loss (est.)", f"{path_loss_db:.1f} dB" if path_loss_db else "—")
    c3.metric("Measured RSSI", f"{rssi_dbm:.1f} dBm" if rssi_dbm else "—")
    c4.metric("Model RSSI (TX−PL)", f"{est_rx_pwr:.1f} dBm" if est_rx_pwr else "—")

    prop_reasoning = (
        f"The signal originates at {tx_power_dbm:.0f} dBm. Path loss over {distance_m:.1f} m is estimated at "
        f"{path_loss_db:.1f} dB (model). The **measured RSSI** from telemetry is {rssi_dbm:.1f} dBm — this is the "
        f"authoritative value used for SNR and QoE calculations in the simulator."
    )
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
    c1.metric("Packet Error Rate (PER)", f"{retry_pct}%")
    c2.metric("Packet Loss (Est)", f"{pkt_loss_pct}%")
    c3.metric("Airtime Utilization", f"{airtime_pct}%")
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
    st.markdown("*(Uses recommendation engine expected_qoe_gain when available)*")
    if action == "NONE":
        st.info("System is operating optimally. No metric changes predicted.")
    else:
        qoe_after = min(100.0, (qoe_score or 0) + exp_gain)
        df_impact = pd.DataFrame([
            {"Metric": "QoE Score", "Current": f"{qoe_score:.1f}/100" if qoe_score else "—", "Predicted": f"{qoe_after:.1f}/100", "Change": f"+{exp_gain:.1f}"},
            {"Metric": "Configuration", "Current": cur_val, "Predicted": rec_val, "Change": "Recommended"}
        ])
        st.dataframe(df_impact, hide_index=True, use_container_width=True)
        
        st.markdown(f"<br>**Expected QoE Gain:** +{exp_gain:.1f} pts", unsafe_allow_html=True)

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
        
        ### Packet Error Rate (PER)
        **Source:** `WiFi6Phy.compute_per()` averaged across clients (stored as `retry_rate` in telemetry).
        - **Current PER:** {retry}%
        - **Airtime Utilization:** {airtime}%
        - **Reason:** PER reflects PHY-layer decode failures driven by SNR and interference.
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

    path_loss_db  = None
    est_rx_pwr    = None

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
    # Removed estimate_post_action_impact

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

    # ── Fetch ALL data once per render cycle (Single Immutable Snapshot) ──
    telemetry_data = fetch_from_api("/telemetry",       params={"ap_id": selected_ap, "limit": 100})
    recs           = fetch_from_api("/recommendations", params={"limit": 5, "ap_id": selected_ap})
    alerts         = fetch_from_api("/alerts",          params={"limit": 50, "ap_id": selected_ap})
    history        = fetch_from_api("/scenario/history", params={"ap_id": selected_ap, "limit": 5})

    if not telemetry_data:
        st.info("ℹ️  No telemetry data yet. Trigger a simulation step or wait for the auto-loop.")
    else:
        # Build immutable snapshot
        df = pd.DataFrame(telemetry_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        latest_row = df.iloc[-1].to_dict()
        top_rec    = recs[0] if recs else None
        
        # Scenario Locking
        active_scenario = latest_row.get("scenario_name", "Unknown")

        # Scenario Event Timeline
        st.markdown("### 📋 Scenario Event Timeline")
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
