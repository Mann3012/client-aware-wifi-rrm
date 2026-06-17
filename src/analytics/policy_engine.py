import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load config thresholds
load_dotenv()
HIGH_RETRY_RATE_THRESHOLD = float(os.getenv("HIGH_RETRY_RATE_THRESHOLD", 0.15))
HIGH_AIRTIME_UTILIZATION_THRESHOLD = float(os.getenv("HIGH_AIRTIME_UTILIZATION_THRESHOLD", 0.70))
LOW_RSSI_THRESHOLD = float(os.getenv("LOW_RSSI_THRESHOLD", -75.0))
LOW_SNR_THRESHOLD = float(os.getenv("LOW_SNR_THRESHOLD", 15.0))
HIGH_NOISE_FLOOR_THRESHOLD = float(os.getenv("HIGH_NOISE_FLOOR_THRESHOLD", -85.0))

logger = logging.getLogger("RRM.Policy")

class RRMPolicyEngine:
    """
    Rule-based engine that evaluates Access Point telemetry metrics and alerts
    to generate Radio Resource Management (RRM) optimization recommendations.
    """
    def __init__(self):
        # Define channel lists for alternative selection
        self.channels_2_4ghz = [1, 6, 11]
        self.channels_5ghz = [36, 40, 44, 48, 149, 153, 157, 161]

    def evaluate(self, telemetry: Dict[str, Any], active_alerts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Evaluates the latest telemetry metrics and active alerts for an AP.
        Returns a dictionary representing a Recommendation if action is needed, otherwise None.
        """
        ap_id = telemetry["ap_id"]
        current_channel = telemetry["channel"]
        rssi = telemetry["rssi"]
        snr = telemetry["snr"]
        noise_floor = telemetry["noise_floor"]
        airtime = telemetry["airtime_utilization"]
        retry_rate = telemetry["retry_rate"]
        clients = telemetry["client_count"]

        # Parse alert types for quick lookups
        alert_types = {alert["alert_type"] for alert in active_alerts}

        # --- RULE 1: Channel Change due to high interference or congestion ---
        # Trigger conditions:
        # - Severe interference alert (noise floor spike)
        # - Both retry rate spike AND airtime congestion alerts are active
        # - Telemetry values exceed thresholds directly
        is_high_interference = "abnormal_interference" in alert_types or noise_floor >= HIGH_NOISE_FLOOR_THRESHOLD
        is_congested_loss = ("retry_spike" in alert_types and "airtime_congestion" in alert_types) or \
                            (retry_rate >= HIGH_RETRY_RATE_THRESHOLD and airtime >= HIGH_AIRTIME_UTILIZATION_THRESHOLD)

        if is_high_interference or is_congested_loss:
            recommended_channel = self._select_alternative_channel(current_channel)
            reason = ""
            confidence = 0.90
            
            if is_high_interference:
                reason = f"Noise floor is critical ({noise_floor} dBm >= threshold {HIGH_NOISE_FLOOR_THRESHOLD} dBm). Severe co-channel or non-WiFi interference detected."
                confidence = 0.95
            else:
                reason = f"Severe airtime congestion ({int(airtime*100)}%) combined with high client packet retry rate ({int(retry_rate*100)}%). Channel is saturated."

            return {
                "ap_id": ap_id,
                "action": "CHANNEL_CHANGE",
                "current_value": str(current_channel),
                "recommended_value": str(recommended_channel),
                "confidence": confidence,
                "reason": reason
            }

        # --- RULE 2: Channel Width Adjustment ---
        # Trigger conditions:
        # - High congestion/retry rate: reduce channel width to 20MHz to improve SNR and decrease collision space.
        # - Very low utilization & moderate client count: expand channel width to maximize throughput.
        if airtime >= HIGH_AIRTIME_UTILIZATION_THRESHOLD and retry_rate >= 0.10:
            # Recommend narrowing the width
            # Note: For simplicity in prototype, we represent width configurations as strings: "20MHz", "40MHz", "80MHz"
            # In a real system, we track the current channel width. We assume a default starting width of 80MHz.
            return {
                "ap_id": ap_id,
                "action": "WIDTH_ADJUST",
                "current_value": "80MHz",
                "recommended_value": "20MHz",
                "confidence": 0.85,
                "reason": f"High airtime utilization ({int(airtime*100)}%) and elevated retries. Reducing channel width to 20MHz increases signal robustness and reduces interference vulnerability."
            }
        
        elif airtime <= 0.25 and clients >= 1 and clients <= 5:
            return {
                "ap_id": ap_id,
                "action": "WIDTH_ADJUST",
                "current_value": "20MHz",
                "recommended_value": "80MHz",
                "confidence": 0.80,
                "reason": f"Channel airtime utilization is low ({int(airtime*100)}%) with a light client load ({clients} clients). Increasing channel width to 80MHz to maximize client throughput capability."
            }

        # --- RULE 3: Transmit (Tx) Power Adjustment ---
        # Trigger conditions:
        # - Low RSSI/SNR with active clients: increase Tx power to expand coverage and improve signal.
        # - High client density but RSSI/SNR are very strong: decrease Tx power to shrink cell size and reduce co-channel interference.
        if clients > 0:
            if rssi <= LOW_RSSI_THRESHOLD or snr <= LOW_SNR_THRESHOLD:
                # Signal is weak, suggest increasing Tx power
                # Tx power values modeled as string, e.g. "14dBm" -> "20dBm"
                return {
                    "ap_id": ap_id,
                    "action": "POWER_ADJUST",
                    "current_value": "14dBm",
                    "recommended_value": "20dBm",
                    "confidence": 0.80,
                    "reason": f"Average client RSSI ({rssi} dBm) or SNR ({snr} dB) is critically low. Increasing Tx power to 20dBm to restore coverage."
                }
            elif clients >= 15 and rssi >= -55.0 and snr >= 30.0:
                # High density, very strong signals. Suggest reducing Tx power.
                return {
                    "ap_id": ap_id,
                    "action": "POWER_ADJUST",
                    "current_value": "20dBm",
                    "recommended_value": "12dBm",
                    "confidence": 0.75,
                    "reason": f"High client density ({clients} clients) with highly redundant signal strength (RSSI: {rssi} dBm). Lowering Tx power to 12dBm to minimize co-channel interference with adjacent cells."
                }

        # No RRM action required
        return None

    def _select_alternative_channel(self, current_channel: int) -> int:
        """Helper to pick a channel in the same band that differs from the current channel."""
        if current_channel in self.channels_2_4ghz:
            options = [ch for ch in self.channels_2_4ghz if ch != current_channel]
            return random_choice_or_default(options, 6)
        else:
            options = [ch for ch in self.channels_5ghz if ch != current_channel]
            return random_choice_or_default(options, 149)

def random_choice_or_default(options: List[int], default: int) -> int:
    """Helper function to pick random alternative or fall back to default."""
    import random
    if not options:
        return default
    return random.choice(options)
