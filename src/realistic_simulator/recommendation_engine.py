class RecommendationEngine:
    """
    Analyzes telemetry to generate actionable RRM recommendations.
    Uses causal heuristics favored by network engineers.
    """

    @staticmethod
    def recommend_action(retry_rate: float, snr: float, airtime_utilization: float, qoe_score: float, distance_meters: float, has_active_interference: bool) -> str:
        """
        Determines the best RRM action based on the current state.
        
        Args:
            retry_rate: Retry rate (0.0 to 1.0)
            snr: Signal-to-Noise Ratio in dB
            airtime_utilization: Airtime utilization (0.0 to 100.0)
            qoe_score: Quality of Experience Score (0 to 100)
            distance_meters: Average client distance in meters
            has_active_interference: True if an external interference event is active
            
        Returns:
            A string recommendation (e.g., CHANNEL_CHANGE, POWER_INCREASE, NONE)
        """
        
        # Rule 1: High Interference + Low SNR -> Change Channel to escape noise
        if has_active_interference and retry_rate > 0.15 and snr < 25.0:
            return "CHANNEL_CHANGE"
            
        # Rule 2: High Utilization + Poor QoE -> Steer clients or reduce width to increase spectral efficiency
        if airtime_utilization > 80.0 and qoe_score < 60.0:
            return "CLIENT_STEERING"
            
        # Rule 3: High Distance + Low SNR -> Increase AP Tx Power
        if distance_meters > 20.0 and snr < 20.0:
            return "POWER_INCREASE"
            
        # Rule 4: High SNR + High Utilization -> Reduce Channel Width (better reuse)
        if snr > 35.0 and airtime_utilization > 75.0:
            return "WIDTH_REDUCTION"
            
        # Rule 5: Excellent QoE but very high power/SNR -> Decrease power to save battery and reduce neighbor interference
        if qoe_score > 90.0 and snr > 45.0 and distance_meters < 10.0:
            return "POWER_DECREASE"

        return "NONE"
