from typing import List, Dict

class RecommendationEngine:
    """
    Analyzes telemetry to generate actionable RRM recommendations.
    Uses causal heuristics favored by network engineers.
    Returns a ranked list of actions based on confidence.
    """

    @staticmethod
    def recommend_action(
        scenario_name: str,
        root_cause: str,
        noise_floor: float,
        snr: float,
        retry_rate: float,
        airtime_utilization: float,
        qoe_score: float,
        distance_meters: float,
        rssi: float,
        client_count: int
    ) -> List[Dict]:
        """
        Determines the best RRM actions based on the current state.
        Returns a list of dicts: {"action", "root_cause", "reason", "confidence", "expected_qoe_gain"}
        """
        recommendations = []
        
        causal_chain_str = f"""Scenario: {scenario_name}
Noise Floor: {noise_floor:.1f} dBm
RSSI: {rssi:.1f} dBm
SNR: {snr:.1f} dB
Retry Rate: {retry_rate * 100.0:.1f}%
QoE: {qoe_score:.1f}"""

        # Rule 1: High Interference + Low SNR -> Change Channel (Non-WiFi Interference)
        # Elevated noise floor and not co-channel WiFi congestion (Neighbor AP)
        if noise_floor >= -90.0 and root_cause != "Neighbor AP":
            is_microwave = (root_cause == "MICROWAVE" or noise_floor >= -82.0)
            recommendations.append({
                "action": "CHANNEL_CHANGE",
                "root_cause": root_cause if root_cause and root_cause != "None" else "HIGH_NOISE",
                "reason": causal_chain_str + f"\nNon-WiFi interference detected (Noise Floor: {noise_floor:.1f} dBm). Move to a clean channel.",
                "confidence": 0.95 if is_microwave else 0.92,
                "expected_qoe_gain": 20.0 if is_microwave else 15.0
            })
            
        # Rule 2: Neighbor AP Co-channel interference -> Load Balance
        if root_cause == "Neighbor AP" or root_cause == "CO_CHANNEL_INTERFERENCE":
            recommendations.append({
                "action": "LOAD_BALANCE",
                "root_cause": "CO_CHANNEL_INTERFERENCE",
                "reason": causal_chain_str + "\nCo-channel interference from neighbor AP. Re-steer clients or balance load to other bands.",
                "confidence": 0.93,
                "expected_qoe_gain": 15.0
            })
            
        # Rule 3: Crowded / High client density congestion -> Reduce Channel Width
        if client_count >= 20 and airtime_utilization > 70.0:
            recommendations.append({
                "action": "WIDTH_ADJUST",
                "root_cause": "CLIENT_CONGESTION",
                "reason": causal_chain_str + f"\nHigh client density ({client_count}) causing airtime congestion ({airtime_utilization:.1f}%). Reduce channel width to gain SNR and reduce overlapping interference.",
                "confidence": 0.94,
                "expected_qoe_gain": 15.0
            })
            # Also add LOAD_BALANCE as secondary recommendation
            recommendations.append({
                "action": "LOAD_BALANCE",
                "root_cause": "CLIENT_CONGESTION",
                "reason": causal_chain_str + f"\nSteer clients to adjacent APs/bands to relieve local channel capacity.",
                "confidence": 0.88,
                "expected_qoe_gain": 12.0
            })

        # Rule 4: Weak Signal -> Increase Power
        if (rssi < -78.0 or distance_meters > 22.0) and noise_floor < -90.0:
            recommendations.append({
                "action": "POWER_INCREASE",
                "root_cause": "WEAK_SIGNAL",
                "reason": causal_chain_str + f"\nLow RSSI ({rssi:.1f} dBm) at distance {distance_meters:.1f}m. Increase AP transmission power to improve SNR.",
                "confidence": 0.90,
                "expected_qoe_gain": 18.0
            })
            
        if not recommendations:
            recommendations.append({
                "action": "NONE",
                "root_cause": "NONE",
                "reason": "Operating optimally. No action required.",
                "confidence": 1.0,
                "expected_qoe_gain": 0.0
            })
            
        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations
