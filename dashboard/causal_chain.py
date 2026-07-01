"""
Causal metric chain helpers for the Streamlit dashboard (Iteration 6).

Pure functions that derive explainability content from live telemetry and
recommendation API payloads. Formulas align with the physics simulator where
noted; predicted impact uses recommendation expected_qoe_gain when available.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def normalize_interference_label(int_type: Optional[str]) -> str:
    """Map simulator interference_type codes to human-readable labels."""
    if not int_type or int_type in ("None", "none", ""):
        return "None"
    mapping = {
        "BLE": "Bluetooth",
        "MICROWAVE": "Microwave",
        "Neighbor AP": "Neighbor AP",
        "CO_CHANNEL_INTERFERENCE": "Neighbor AP",
        "CLIENT_CONGESTION": "Client Congestion",
        "WEAK_SIGNAL": "Weak Signal",
    }
    return mapping.get(int_type, int_type.replace("_", " ").title())


def interference_matches(int_type: Optional[str], *keywords: str) -> bool:
    """Case-insensitive substring match against normalized interference label."""
    if not int_type or int_type in ("None", "none", ""):
        return False
    label = normalize_interference_label(int_type).lower()
    raw = int_type.lower()
    return any(k.lower() in label or k.lower() in raw for k in keywords)


def parse_spectrum_snapshot(raw: Any) -> Optional[dict]:
    """Parse spectrum_snapshot JSON string from telemetry API."""
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        import json
        return json.loads(raw)
    except (TypeError, ValueError):
        return None



def get_snr_label(snr):
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


def format_root_cause_label(root_cause: Optional[str]) -> str:
    if not root_cause or root_cause in ("NONE", "None", ""):
        return ""
    return root_cause.replace("_", " ").title()


def build_dynamic_causal_chain(root_cause: str, action: str, telemetry: dict) -> str:
    def _cv(v, d=1, s=""): return f"{round(float(v),d)}{s}" if v is not None else "—"
    
    path_loss_db = telemetry.get("path_loss_db")
    rssi_dbm = telemetry.get("rssi")
    snr_db = telemetry.get("snr")
    retry_pct = round((telemetry.get("retry_rate", 0) or 0) * 100, 1)
    qoe_score = telemetry.get("qoe_score")
    airtime_pct = round((telemetry.get("airtime_utilization", 0) or 0) * 100, 1)
    
    if "Coverage" in root_cause:
        flow = f"Distance & Obstacles\n&darr;\nHigh Path Loss ({_cv(path_loss_db, 1, ' dB')})\n&darr;\nWeak Received Signal ({_cv(rssi_dbm, 1, ' dBm')})\n&darr;\nReduced SNR ({_cv(snr_db, 1, ' dB')})\n&darr;\nLower MCS\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nThroughput Loss\n&darr;\n{action} Recommended"
    elif "Bluetooth" in root_cause:
        flow = f"Bluetooth Activity\n&darr;\nBurst RF Interference\n&darr;\nFrame Collisions\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nReduced Efficiency\n&darr;\n{action} Recommended"
    elif "Microwave" in root_cause:
        flow = f"Microwave Emissions\n&darr;\nBroadband RF Noise\n&darr;\nPacket Corruption\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nThroughput Reduction\n&darr;\n{action} Recommended"
    elif "Neighbor" in root_cause or "Co-Channel" in root_cause:
        flow = f"Neighbor AP Activity\n&darr;\nCo-channel Contention\n&darr;\nAirtime Competition\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nReduced Capacity\n&darr;\n{action} Recommended"
    elif "Congestion" in root_cause:
        flow = f"High Client Density\n&darr;\nAirtime Saturation ({airtime_pct}%)\n&darr;\nChannel Contention\n&darr;\nCollision Probability\n&darr;\nBackoff Delays\n&darr;\nRetransmissions ({retry_pct}%)\n&darr;\nLatency Increase & QoE Reduction\n&darr;\n{action} Recommended"
    else:
        flow = f"Optimal Environmental Conditions\n&darr;\nHealthy Signal Quality\n&darr;\nNominal Retransmissions\n&darr;\nStrong User QoE ({_cv(qoe_score, 1, '/100')})\n&darr;\nNo Action Required"

    return flow


def build_justification_text(
    action, rssi, snr, noise_floor, distance_m,
    wall_count, retry_rate, qoe_score, int_type, airtime_frac,
    rec_reason: Optional[str] = None,
):
    """Engineer-grade narrative; prefers recommendation reason when provided."""
    if rec_reason and rec_reason.strip():
        return rec_reason.strip()

    r_val = rssi if rssi is not None else -95.0
    s_val = snr if snr is not None else 0.0
    nf_val = noise_floor if noise_floor is not None else -95.0
    d_val = distance_m if distance_m is not None else 1.0
    w_count = wall_count if wall_count is not None else 0
    w_loss = w_count * 3.0
    ret_rate = retry_rate if retry_rate is not None else 0.0
    qoe = qoe_score if qoe_score is not None else 0.0
    airtime = airtime_frac if airtime_frac is not None else 0.0
    interference = normalize_interference_label(int_type)

    rssi_explanation = (
        f"The Received Signal Strength Indicator (RSSI) is measured at {r_val:.1f} dBm. "
        f"Signal attenuation over {d_val:.1f} m includes approximately {w_loss:.1f} dB from {w_count} wall(s)."
    )
    snr_explanation = (
        f"SNR = RSSI − Noise Floor = {r_val:.1f} − ({nf_val:.1f}) = {s_val:.1f} dB. "
        f"At this margin, packet error rate (PER) rises to {ret_rate * 100:.1f}%, degrading QoE to {qoe:.1f}/100."
    )

    if action == "POWER_INCREASE":
        dominant_issue = "Coverage / Obstruction"
        recommendation_action_desc = "Increasing AP transmit power compensates for path loss and restores SNR margin."
    elif action == "CHANNEL_CHANGE":
        dominant_issue = "Interference"
        recommendation_action_desc = (
            f"Migrating to a clean channel avoids {interference} interference "
            f"(noise floor {nf_val:.1f} dBm), recovering SNR and throughput."
        )
    elif action == "LOAD_BALANCE":
        dominant_issue = "Congestion"
        recommendation_action_desc = "Steering clients reduces co-channel contention and airtime utilization."
    elif action == "WIDTH_ADJUST":
        dominant_issue = "Congestion / Capacity"
        recommendation_action_desc = "Narrowing channel width reduces noise bandwidth and improves link stability under congestion."
    elif action == "POWER_DECREASE":
        dominant_issue = "Capacity"
        recommendation_action_desc = "Reducing TX power shrinks cell overlap and improves spectral reuse."
    else:
        dominant_issue = "System Optimal"
        recommendation_action_desc = "No corrective RRM actions are required at this time."

    return (
        f"ENGINEERING TROUBLESHOOTING NOTES:\n\n"
        f"• Propagation & Path Loss:\n{rssi_explanation}\n\n"
        f"• RF Signal Quality:\n{snr_explanation}\n\n"
        f"• Root Cause: {dominant_issue}\n"
        f"• RRM Action Justification: {recommendation_action_desc}"
    )


def estimate_post_action_impact(
    action, rssi, snr, qoe, retry_rate,
    expected_qoe_gain: Optional[float] = None,
):
    """
    Return post-action metrics relying purely on backend predictions.
    """
    qoe_delta = expected_qoe_gain if expected_qoe_gain is not None else 0.0

    def safe_add(v, delta, mn=None, mx=None):
        if v is None:
            return None
        r = round(v + delta, 2)
        if mn is not None:
            r = max(mn, r)
        if mx is not None:
            r = min(mx, r)
        return r

    return {
        "rssi_before": rssi,
        "rssi_after": rssi,
        "snr_before": snr,
        "snr_after": snr,
        "qoe_before": qoe,
        "qoe_after": safe_add(qoe, qoe_delta, mx=100.0),
        "retry_before": retry_rate,
        "retry_after": retry_rate,
    }
