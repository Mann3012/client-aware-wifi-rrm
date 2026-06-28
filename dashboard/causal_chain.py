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


def derive_root_cause_ranked(
    rssi, snr, noise_floor, retry_rate, airtime_frac, int_type, distance_m,
    rec_root_cause: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Ranked root causes. When recommendation engine provides root_cause, it
    receives highest priority with recommendation confidence applied later.
    """
    causes: List[Dict[str, Any]] = []

    if rec_root_cause and rec_root_cause not in ("NONE", "None", ""):
        label = format_root_cause_label(rec_root_cause)
        if "MICROWAVE" in rec_root_cause.upper():
            causes.append({"label": f"Interference ({normalize_interference_label('MICROWAVE')})",
                           "conf": 0.95, "reason": "Broadband RF noise emission detected by recommendation engine."})
        elif "BLE" in rec_root_cause.upper() or "BLUETOOTH" in rec_root_cause.upper():
            causes.append({"label": "Interference (Bluetooth)",
                           "conf": 0.95, "reason": "Bursty non-WiFi interference detected; overlaps with Wi-Fi frames."})
        elif "NEIGHBOR" in rec_root_cause.upper() or "CO_CHANNEL" in rec_root_cause.upper():
            causes.append({"label": "Co-Channel Contention (Neighbor AP)",
                           "conf": 0.93, "reason": "Neighbor AP traffic increases contention and airtime competition."})
        elif "CONGESTION" in rec_root_cause.upper():
            causes.append({"label": "Congestion (High Density)",
                           "conf": 0.94, "reason": "Channel is heavily utilized by active traffic, causing medium contention."})
        elif "WEAK" in rec_root_cause.upper() or "COVERAGE" in rec_root_cause.upper():
            causes.append({"label": "Coverage (Distance + Path Loss)",
                           "conf": 0.90, "reason": "Weak signal due to propagation distance and path loss."})
        else:
            causes.append({"label": label, "conf": 0.90,
                           "reason": f"Recommendation engine identified root cause: {label}."})

    if interference_matches(int_type, "bluetooth", "ble"):
        causes.append({"label": "Interference (Bluetooth)", "conf": 0.95,
                       "reason": "Bursty non-WiFi interference detected; overlaps with Wi-Fi frames."})
    elif interference_matches(int_type, "microwave"):
        causes.append({"label": "Interference (Microwave)", "conf": 0.95,
                       "reason": "Broadband RF noise emission detected."})
    elif interference_matches(int_type, "neighbor", "co_channel"):
        causes.append({"label": "Co-Channel Contention (Neighbor AP)", "conf": 0.92,
                       "reason": "Neighbor AP traffic increases contention and airtime competition."})
    elif int_type and int_type not in ("None", "none", ""):
        causes.append({"label": f"Interference ({normalize_interference_label(int_type)})", "conf": 0.90,
                       "reason": "Active non-WiFi interference detected."})
    elif noise_floor is not None and noise_floor >= -90:
        causes.append({"label": "Interference (Elevated Noise)", "conf": 0.85,
                       "reason": "Elevated noise floor independent of client traffic."})
    else:
        causes.append({"label": "Interference", "conf": 0.15,
                       "reason": "Noise floor is clean at the AP."})

    if rssi is not None and rssi < -78:
        if distance_m is not None and distance_m > 20:
            causes.append({"label": "Coverage (Distance + Path Loss)", "conf": 0.90,
                           "reason": "Weak signal due to propagation distance and path loss."})
        else:
            causes.append({"label": "Coverage (Weak Signal)", "conf": 0.88,
                           "reason": "Weak signal despite proximity (possible obstruction)."})
    else:
        causes.append({"label": "Coverage", "conf": 0.18,
                       "reason": "RSSI remains strong, suggesting adequate signal propagation."})

    if airtime_frac is not None and airtime_frac > 0.75:
        causes.append({"label": "Congestion (High Density)", "conf": 0.93,
                       "reason": "Channel is heavily utilized by active traffic, causing medium contention."})
    else:
        causes.append({"label": "Congestion", "conf": 0.20,
                       "reason": "Airtime utilization is nominal, indicating no channel saturation."})

    # Deduplicate by label, keep highest confidence
    seen: Dict[str, Dict] = {}
    for c in causes:
        key = c["label"]
        if key not in seen or c["conf"] > seen[key]["conf"]:
            seen[key] = c
    causes = sorted(seen.values(), key=lambda x: x["conf"], reverse=True)

    if causes[0]["conf"] < 0.50:
        causes.insert(0, {"label": "System Optimal", "conf": 0.99,
                         "reason": "All metrics are within healthy nominal parameters."})

    return causes


def derive_root_cause(rssi, snr, noise_floor, retry_rate, airtime_frac, int_type, distance_m):
    ranked = derive_root_cause_ranked(rssi, snr, noise_floor, retry_rate, airtime_frac, int_type, distance_m)
    return ranked[0]["label"], ranked[0]["conf"]


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
