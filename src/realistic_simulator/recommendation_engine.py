from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Diagnosis:
    root_cause: str
    confidence: float
    recommendation: str
    expected_qoe_gain: float
    expected_retry_reduction: float

DIAGNOSIS_THRESHOLDS = {
    "coverage_path_loss": 90.0,
    "coverage_retry": 0.15,
    "healthy_qoe": 80.0,
    "airtime_congestion": 70.0,
    "congestion_client_count": 20,
    "co_channel_airtime": 40.0,
    "microwave_noise": -85.0,
    "bluetooth_retry": 0.10,
    "clean_noise_floor": -90.0,
    "weak_signal_rssi": -75.0,
    "healthy_retry": 0.05,
}

class DiagnosticEngine:
    """
    Evaluates telemetry to infer root causes using a scoring system.
    """
    def diagnose(
        self,
        path_loss_db: float,
        interference_type: str,
        noise_floor: float,
        retry_rate: float,
        qoe_score: float,
        airtime_utilization: float,
        client_count: int,
        rssi: float,
    ) -> List[Diagnosis]:
        diagnoses = []
        
        # Calculate dynamic expected impact based on QoE gap
        qoe_gap = max(0, DIAGNOSIS_THRESHOLDS["healthy_qoe"] - qoe_score)
        base_expected_qoe_gain = min(25.0, qoe_gap * 0.75)
        base_expected_retry_reduction = min(20.0, retry_rate * 100 * 0.5)

        # 1. Coverage Problem (Weak Signal)
        coverage_score = 0.0
        if path_loss_db > DIAGNOSIS_THRESHOLDS["coverage_path_loss"]:
            overshoot = (path_loss_db - DIAGNOSIS_THRESHOLDS["coverage_path_loss"]) / DIAGNOSIS_THRESHOLDS["coverage_path_loss"]
            coverage_score = min(0.99, 0.80 + overshoot * 0.15)
        elif retry_rate > DIAGNOSIS_THRESHOLDS["coverage_retry"] and qoe_score < DIAGNOSIS_THRESHOLDS["healthy_qoe"] and noise_floor < DIAGNOSIS_THRESHOLDS["clean_noise_floor"]:
            coverage_score = min(0.95, 0.80 + (retry_rate - DIAGNOSIS_THRESHOLDS["coverage_retry"]) * 0.5)
        elif rssi < DIAGNOSIS_THRESHOLDS["weak_signal_rssi"] and noise_floor < DIAGNOSIS_THRESHOLDS["clean_noise_floor"]:
            overshoot = (DIAGNOSIS_THRESHOLDS["weak_signal_rssi"] - rssi) / abs(DIAGNOSIS_THRESHOLDS["weak_signal_rssi"])
            coverage_score = min(0.90, 0.75 + overshoot)
        
        if coverage_score > 0:
            diagnoses.append(Diagnosis(
                root_cause="Coverage Problem",
                confidence=coverage_score,
                recommendation="POWER_INCREASE",
                expected_qoe_gain=base_expected_qoe_gain,
                expected_retry_reduction=base_expected_retry_reduction
            ))

        # 2. Client Congestion
        congestion_score = 0.0
        if airtime_utilization > DIAGNOSIS_THRESHOLDS["airtime_congestion"] and client_count >= DIAGNOSIS_THRESHOLDS["congestion_client_count"]:
            overshoot = (airtime_utilization - DIAGNOSIS_THRESHOLDS["airtime_congestion"]) / DIAGNOSIS_THRESHOLDS["airtime_congestion"]
            congestion_score = min(0.99, 0.85 + overshoot * 0.2)
        elif airtime_utilization > 85.0:
            congestion_score = 0.85
            
        if congestion_score > 0:
            diagnoses.append(Diagnosis(
                root_cause="Client Congestion",
                confidence=congestion_score,
                recommendation="WIDTH_ADJUST",
                expected_qoe_gain=base_expected_qoe_gain * 1.2, # slightly higher expected gain for congestion relief
                expected_retry_reduction=base_expected_retry_reduction * 0.8
            ))

        # 3. Co-Channel Interference (Neighbor AP)
        co_channel_score = 0.0
        if interference_type in ["Neighbor AP", "CO_CHANNEL_INTERFERENCE"] and airtime_utilization > DIAGNOSIS_THRESHOLDS["co_channel_airtime"]:
            overshoot = (airtime_utilization - DIAGNOSIS_THRESHOLDS["co_channel_airtime"]) / DIAGNOSIS_THRESHOLDS["co_channel_airtime"]
            co_channel_score = min(0.98, 0.85 + overshoot * 0.2)

        if co_channel_score > 0:
            diagnoses.append(Diagnosis(
                root_cause="Co-Channel Interference",
                confidence=co_channel_score,
                recommendation="LOAD_BALANCE",
                expected_qoe_gain=base_expected_qoe_gain,
                expected_retry_reduction=base_expected_retry_reduction * 0.5
            ))

        # 4. Microwave / Broadband Noise
        microwave_score = 0.0
        if noise_floor >= DIAGNOSIS_THRESHOLDS["microwave_noise"] and interference_type != "Neighbor AP":
            overshoot = (noise_floor - DIAGNOSIS_THRESHOLDS["microwave_noise"]) / abs(DIAGNOSIS_THRESHOLDS["microwave_noise"])
            microwave_score = min(0.99, 0.85 + overshoot * 2.0)
        elif interference_type == "MICROWAVE" and retry_rate > 0.05:
            microwave_score = 0.90

        if microwave_score > 0:
            diagnoses.append(Diagnosis(
                root_cause="Microwave Interference",
                confidence=microwave_score,
                recommendation="CHANNEL_CHANGE",
                expected_qoe_gain=base_expected_qoe_gain * 1.5,
                expected_retry_reduction=base_expected_retry_reduction * 1.5
            ))

        # 5. Bluetooth Interference
        bluetooth_score = 0.0
        if interference_type == "BLE" and retry_rate > DIAGNOSIS_THRESHOLDS["bluetooth_retry"]:
            overshoot = (retry_rate - DIAGNOSIS_THRESHOLDS["bluetooth_retry"]) / DIAGNOSIS_THRESHOLDS["bluetooth_retry"]
            bluetooth_score = min(0.98, 0.85 + overshoot * 0.5)
        elif interference_type == "BLE":
            bluetooth_score = 0.85

        if bluetooth_score > 0:
            diagnoses.append(Diagnosis(
                root_cause="Bluetooth Interference",
                confidence=bluetooth_score,
                recommendation="CHANNEL_CHANGE",
                expected_qoe_gain=base_expected_qoe_gain * 1.2,
                expected_retry_reduction=base_expected_retry_reduction * 1.2
            ))

        # Fallback / Catch-all for general degradation
        if not diagnoses and qoe_score < DIAGNOSIS_THRESHOLDS["healthy_qoe"]:
            if retry_rate > DIAGNOSIS_THRESHOLDS["healthy_retry"]:
                diagnoses.append(Diagnosis(
                    root_cause="Unclassified Degradation",
                    confidence=0.60,
                    recommendation="POWER_INCREASE",
                    expected_qoe_gain=base_expected_qoe_gain,
                    expected_retry_reduction=base_expected_retry_reduction
                ))

        # If no issues detected, it is healthy
        if not diagnoses:
            diagnoses.append(Diagnosis(
                root_cause="Healthy",
                confidence=0.99,
                recommendation="NONE",
                expected_qoe_gain=0.0,
                expected_retry_reduction=0.0
            ))

        # Sort by confidence descending
        diagnoses.sort(key=lambda d: d.confidence, reverse=True)
        return diagnoses

class RecommendationEngine:
    """
    Delegates to the DiagnosticEngine to evaluate telemetry and returns
    recommendations matching the legacy dictionary format for API compatibility.
    """
    @staticmethod
    def recommend_action(
        path_loss_db: float,
        interference_type: str,
        noise_floor: float,
        retry_rate: float,
        qoe_score: float,
        airtime_utilization: float,
        client_count: int,
        rssi: float,
        # Legacy parameters for compatibility (ignored in diagnosis logic)
        scenario_name: str = "",
        root_cause: str = "",
        snr: float = 0.0,
        distance_meters: float = 0.0,
    ) -> List[Dict]:
        engine = DiagnosticEngine()
        diagnoses = engine.diagnose(
            path_loss_db=path_loss_db,
            interference_type=interference_type,
            noise_floor=noise_floor,
            retry_rate=retry_rate,
            qoe_score=qoe_score,
            airtime_utilization=airtime_utilization,
            client_count=client_count,
            rssi=rssi
        )

        recommendations = []
        for d in diagnoses:
            recommendations.append({
                "action": d.recommendation,
                "root_cause": d.root_cause,
                # Provide a structured reason matching the new expected layout
                "reason": f"Expected QoE +{d.expected_qoe_gain:.0f}%, Expected Retry -{d.expected_retry_reduction:.0f}%",
                "confidence": d.confidence,
                "expected_qoe_gain": d.expected_qoe_gain,
                "expected_retry_reduction": d.expected_retry_reduction,
            })
            
        return recommendations
