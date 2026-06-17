import math
import json
from typing import List, Optional
from dataclasses import asdict

from src.realistic_simulator.models import (
    APState, ClientState, QoE, InterferenceEvent, TelemetryRecord
)
from src.realistic_simulator.recommendation_engine import RecommendationEngine

class TelemetrySimulator:
    """
    Generates realistic Wi-Fi telemetry based on networking physics and heuristics.
    """
    
    # Research-backed: Log-Distance Path Loss Model parameters
    D0_METERS = 1.0
    RSSI_D0 = -35.0  # dBm at 1 meter
    PATH_LOSS_EXPONENT = 3.0  # Typical for indoor office/home environments
    
    # Engineering Approximation: Channel capacities in Mbps
    CAPACITY_MBPS = {
        20: 144.0,   # e.g., 2x2 802.11n/ac at 20MHz
        40: 300.0,   # e.g., 2x2 802.11n/ac at 40MHz
        80: 866.0    # e.g., 2x2 802.11ac at 80MHz
    }

    def __init__(self, ap_state: APState):
        self.ap = ap_state

    def calculate_rssi(self, distance_meters: float) -> float:
        """
        (A) Research-backed networking model
        Log-Distance Path Loss Model: RSSI(d) = RSSI(d0) - 10 * n * log10(d / d0)
        """
        if distance_meters < self.D0_METERS:
            return self.RSSI_D0
            
        loss = 10 * self.PATH_LOSS_EXPONENT * math.log10(distance_meters / self.D0_METERS)
        return self.RSSI_D0 - loss

    def calculate_noise_floor(self, event: Optional[InterferenceEvent]) -> float:
        """
        (B) Engineering approximation
        Base noise floor plus any additive interference from external sources.
        """
        noise = self.ap.base_noise
        if event and event.active:
            noise += event.noise_boost_db
        return noise

    def calculate_snr(self, rssi: float, noise_floor: float) -> float:
        """
        (A) Research-backed networking model
        SNR = RSSI - Noise Floor
        """
        return max(0.0, rssi - noise_floor)

    def calculate_airtime_utilization(self, clients: List[ClientState], event: Optional[InterferenceEvent]) -> float:
        """
        (B) Engineering approximation
        Load fraction based on client demand vs. channel capacity.
        Utilization = (Total Demand / Channel Capacity) * 100
        """
        total_demand = sum(client.demand_mbps for client in clients)
        capacity = self.CAPACITY_MBPS.get(self.ap.channel_width, 144.0)
        
        utilization = (total_demand / capacity) * 100.0
        
        if event and event.active:
            utilization += event.airtime_boost_percent
            
        return min(100.0, max(0.0, utilization))

    def calculate_retry_rate(self, snr: float, utilization: float) -> float:
        """
        (C) Simulation heuristic
        High SNR + Low Airtime -> Low Retry Rate
        Low SNR + High Airtime -> High Retry Rate
        """
        # Base retry rate from SNR (lower SNR -> higher retries)
        if snr > 40.0:
            retry_base = 0.02
        elif snr > 25.0:
            retry_base = 0.05
        elif snr > 15.0:
            retry_base = 0.15
        else:
            retry_base = 0.35
            
        # Utilization multiplier (congestion causes collisions, leading to retries)
        util_factor = 1.0 + (utilization / 100.0) ** 2  # Exponential growth in collisions
        
        retry_rate = retry_base * util_factor
        return min(1.0, max(0.0, retry_rate))

    def calculate_qoe(self, retry_rate: float, snr: float, utilization: float) -> QoE:
        """
        (C) Simulation heuristic
        Creates a 0-100 score based on networking metrics.
        """
        # Start with a perfect score
        score = 100.0
        
        # Penalties
        # 1. High Retry Rate penalty (critical impact on latency/TCP throughput)
        score -= (retry_rate * 100.0)
        
        # 2. Low SNR penalty (limits modulation rate)
        if snr < 25.0:
            score -= (25.0 - snr) * 1.5
            
        # 3. High Utilization penalty (causes jitter and queuing delay)
        if utilization > 70.0:
            score -= (utilization - 70.0) * 0.8
            
        score = min(100.0, max(0.0, score))
        
        if score >= 90.0:
            category = "Excellent"
        elif score >= 70.0:
            category = "Good"
        elif score >= 50.0:
            category = "Fair"
        else:
            category = "Poor"
            
        return QoE(score=score, category=category)

    def generate_telemetry(self, clients: List[ClientState], event: Optional[InterferenceEvent] = None) -> TelemetryRecord:
        """
        Executes the causal pipeline to generate a realistic telemetry snapshot.
        """
        # Aggregate client distance to find average (or use furthest for worst-case)
        if not clients:
            avg_distance = self.D0_METERS
        else:
            avg_distance = sum(c.distance_meters for c in clients) / len(clients)

        # 1. RSSI
        rssi = self.calculate_rssi(avg_distance)
        
        # 2. Noise Floor
        noise = self.calculate_noise_floor(event)
        
        # 3. SNR
        snr = self.calculate_snr(rssi, noise)
        
        # 4. Airtime Utilization
        utilization = self.calculate_airtime_utilization(clients, event)
        
        # 5. Retry Rate
        retry_rate = self.calculate_retry_rate(snr, utilization)
        
        # 6. QoE Score
        qoe = self.calculate_qoe(retry_rate, snr, utilization)
        
        # 7. Recommendations
        has_active_interference = (event is not None and event.active)
        recommendation = RecommendationEngine.recommend_action(
            retry_rate=retry_rate,
            snr=snr,
            airtime_utilization=utilization,
            qoe_score=qoe.score,
            distance_meters=avg_distance,
            has_active_interference=has_active_interference
        )
        
        return TelemetryRecord(
            ap_id=self.ap.ap_id,
            channel=self.ap.channel,
            client_count=len(clients),
            rssi=rssi,
            noise_floor=noise,
            snr=snr,
            airtime_utilization=utilization,
            retry_rate=retry_rate,
            qoe_score=qoe.score,
            qoe_category=qoe.category,
            recommendation=recommendation
        )

# Example Usage for Validation
if __name__ == "__main__":
    ap = APState(ap_id="AP_001_Floor1", channel=36, channel_width=40, base_noise=-95.0)
    sim = TelemetrySimulator(ap)
    
    clients = [
        ClientState(client_id="C1", distance_meters=5.0, demand_mbps=20.0),
        ClientState(client_id="C2", distance_meters=15.0, demand_mbps=50.0),
        ClientState(client_id="C3", distance_meters=25.0, demand_mbps=80.0),
    ]
    
    print("--- SCENARIO 1: NORMAL CONDITIONS ---")
    record_normal = sim.generate_telemetry(clients, event=None)
    print(json.dumps(record_normal.to_dict(), indent=2))
    
    print("\n--- SCENARIO 2: MICROWAVE INTERFERENCE ---")
    microwave = InterferenceEvent(
        event_type="Microwave",
        noise_boost_db=15.0,
        airtime_boost_percent=0.0,
        duration_minutes=5,
        active=True
    )
    record_microwave = sim.generate_telemetry(clients, event=microwave)
    print(json.dumps(record_microwave.to_dict(), indent=2))
