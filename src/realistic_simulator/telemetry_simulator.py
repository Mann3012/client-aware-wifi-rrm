import math
import random
import json
from typing import List, Optional

from src.realistic_simulator.models import (
    APState, ClientState, QoE, InterferenceEvent, TelemetryRecord
)
from src.realistic_simulator.recommendation_engine import RecommendationEngine
from src.realistic_simulator.scenario_engine import Scenario

class TelemetrySimulator:
    """
    Generates realistic Wi-Fi telemetry based on networking physics and heuristics.
    """
    
    # Path Loss parameters
    D0_METERS = 1.0
    PATH_LOSS_EXPONENT = 3.0  # Typical for indoor office/home environments (n=3)
    WALL_ATTENUATION_DB = 3.0 # Average attenuation per wall (e.g. Drywall)

    def __init__(self, ap_state: APState):
        self.ap = ap_state

    def calculate_distance(self, client: ClientState) -> float:
        """
        Calculates Euclidean distance between AP and client.
        Formula: d = sqrt((x2 - x1)^2 + (y2 - y1)^2)
        """
        dist = math.sqrt((client.x - self.ap.x)**2 + (client.y - self.ap.y)**2)
        return max(self.D0_METERS, dist) # Minimum distance is d0

    def apply_mobility(self, clients: List[ClientState]):
        """
        Simulates random client movement (Random Walk).
        """
        for client in clients:
            client.x += random.uniform(-1.0, 1.0)
            client.y += random.uniform(-1.0, 1.0)

    def calculate_path_loss(self, distance_meters: float, freq_mhz: float) -> float:
        """
        Log-Distance Path Loss Model
        Formula: PL(d) = PL(d0) + 10 * n * log10(d / d0)
        Source: Wireless Communications text, typical indoor propagation.
        Assumptions: n=3.0 (Office), FSPL used only for reference distance d0=1m.
        """
        # 1. Compute reference loss using Free Space Path Loss at 1 meter (0.001 km)
        # PL(dB) = 32.44 + 20*log10(d_km) + 20*log10(freq_MHz)
        pl_d0 = 32.44 + 20 * math.log10(0.001) + 20 * math.log10(freq_mhz)
        
        # 2. Compute Log-Distance loss
        pl_d = pl_d0 + 10 * self.PATH_LOSS_EXPONENT * math.log10(distance_meters / self.D0_METERS)
        return pl_d

    def calculate_rssi(self, distance_meters: float, wall_count: int) -> float:
        """
        Calculates Received Signal Strength Indicator.
        Formula: RSSI = TxPower - PathLoss - WallLoss
        """
        pl = self.calculate_path_loss(distance_meters, self.ap.freq_mhz)
        wall_loss = wall_count * self.WALL_ATTENUATION_DB
        return self.ap.tx_power_dbm - pl - wall_loss

    def calculate_noise_floor(self, scenario: Optional[Scenario]) -> float:
        """
        Base noise floor plus any additive interference from external sources.
        Formula: NoiseFloor = BaseNoise + InterferenceContribution
        """
        noise = self.ap.base_noise
        if scenario and scenario.interference and scenario.interference.active:
            noise += scenario.interference.noise_boost_db
        return noise

    def calculate_snr(self, rssi: float, noise_floor: float) -> float:
        """
        SNR = RSSI - Noise Floor
        Source: Cisco Wireless Design Best Practices
        """
        return max(0.0, rssi - noise_floor)

    def calculate_airtime_utilization(self, clients: List[ClientState], scenario: Optional[Scenario]) -> float:
        """
        Calculates AP Airtime Utilization.
        Formula: Airtime = min(100, (TotalClientDemand / ChannelCapacity) * 100)
        """
        demand_mult = scenario.client_demand_multiplier if scenario else 1.0
        total_demand = sum(client.demand_mbps * demand_mult for client in clients)
        
        utilization = (total_demand / self.ap.channel_capacity_mbps) * 100.0
        
        if scenario and scenario.interference and scenario.interference.active:
            utilization += scenario.interference.airtime_boost_percent
            
        return min(100.0, max(0.0, utilization))

    def calculate_retry_rate(self, snr: float, client_count: int = 1, airtime_utilization: float = 0.0) -> float:
        """
        Calculates retry rate based on both SNR (noise/interference) and airtime utilization/client count (congestion).
        Formula: retry_rate = 1 - (1 - retry_rate_snr) * (1 - retry_rate_congestion)
        Bounded between 0.01 (1%) and 0.80 (80%).
        """
        # 1. SNR-based retries
        retry_percent = min(80.0, max(1.0, 100.0 * math.exp(-0.12 * snr)))
        retry_rate_snr = retry_percent / 100.0  # Fraction (0.01 - 0.80)
        
        # 2. Congestion-based retries
        retry_rate_congestion = 0.50 * (airtime_utilization / 100.0) * (1.0 - math.exp(-0.04 * client_count))
        
        # 3. Combined retry rate
        combined_retry_rate = 1.0 - (1.0 - retry_rate_snr) * (1.0 - retry_rate_congestion)
        return min(0.80, max(0.01, combined_retry_rate))

    def calculate_qoe(self, snr: float, retry_rate: float, noise_floor: float, airtime: float) -> QoE:
        """
        Derived normalized QoE Score.
        Formula: QoE = 0.40 * SNRScore + 0.30 * RetryScore + 0.20 * NoiseScore + 0.10 * ClientLoadScore
        """
        # Sub-scores scaled 0-100
        snr_score = min(100.0, max(0.0, (snr / 35.0) * 100.0))
        
        retry_percent = retry_rate * 100.0
        retry_score = min(100.0, max(0.0, 100.0 - (retry_percent * 1.5))) # 0% retry=100, 66% retry=0
        
        # Noise score: -95dBm is 100, -75dBm is 0
        noise_penalty = max(0.0, noise_floor - self.ap.base_noise)
        noise_score = min(100.0, max(0.0, 100.0 - (noise_penalty * 5.0)))
        
        client_load_score = min(100.0, max(0.0, 100.0 - airtime))
        
        qoe_val = (0.40 * snr_score) + (0.30 * retry_score) + (0.20 * noise_score) + (0.10 * client_load_score)
        
        qoe_val = min(100.0, max(0.0, qoe_val))
        
        if qoe_val >= 85.0:
            category = "Excellent"
        elif qoe_val >= 65.0:
            category = "Good"
        elif qoe_val >= 40.0:
            category = "Fair"
        else:
            category = "Poor"
            
        return QoE(score=qoe_val, category=category)

    def generate_telemetry(self, clients: List[ClientState], scenario: Optional[Scenario] = None) -> TelemetryRecord:
        """
        Executes the causal pipeline: Mobility -> Distance -> PL -> RSSI -> Noise -> SNR -> Retry -> QoE -> Recommendations.
        """
        self.apply_mobility(clients)
        
        # Calculate individual client metrics to find averages
        total_rssi = 0.0
        total_snr = 0.0
        total_retry = 0.0
        total_dist = 0.0
        total_wall = 0
        total_wall_loss = 0.0
        
        noise = self.calculate_noise_floor(scenario)
        client_count = len(clients)
        utilization = self.calculate_airtime_utilization(clients, scenario)
        
        for c in clients:
            dist = self.calculate_distance(c)
            rssi = self.calculate_rssi(dist, c.wall_count)
            snr = self.calculate_snr(rssi, noise)
            retry = self.calculate_retry_rate(snr, client_count=client_count, airtime_utilization=utilization)
            
            total_dist += dist
            total_rssi += rssi
            total_snr += snr
            total_retry += retry
            total_wall += c.wall_count
            total_wall_loss += (c.wall_count * self.WALL_ATTENUATION_DB)
            
        if client_count > 0:
            avg_dist = total_dist / client_count
            avg_rssi = total_rssi / client_count
            avg_snr = total_snr / client_count
            avg_retry = total_retry / client_count
            avg_wall = int(total_wall / client_count)
            avg_wall_loss = total_wall_loss / client_count
        else:
            avg_dist = self.D0_METERS
            avg_rssi = -95.0
            avg_snr = 0.0
            avg_retry = 0.0
            avg_wall = 0
            avg_wall_loss = 0.0
        qoe = self.calculate_qoe(avg_snr, avg_retry, noise, utilization)
        
        has_active_interference = (scenario is not None and scenario.interference is not None and scenario.interference.active)
        
        recommendations = RecommendationEngine.recommend_action(
            scenario_name=scenario.name if scenario else "Normal Office",
            root_cause=scenario.interference_type if scenario else "None",
            noise_floor=noise,
            snr=avg_snr,
            retry_rate=avg_retry,
            airtime_utilization=utilization,
            qoe_score=qoe.score,
            distance_meters=avg_dist,
            rssi=avg_rssi,
            client_count=client_count
        )
        
        return TelemetryRecord(
            ap_id=self.ap.ap_id,
            channel=self.ap.channel,
            client_count=client_count,
            rssi=avg_rssi,
            noise_floor=noise,
            snr=avg_snr,
            airtime_utilization=utilization,
            retry_rate=avg_retry,
            qoe_score=qoe.score,
            qoe_category=qoe.category,
            interference_type=scenario.interference.event_type if has_active_interference else "None",
            distance=avg_dist,
            freq_mhz=self.ap.freq_mhz,
            tx_power=self.ap.tx_power_dbm,
            wall_count=avg_wall,
            wall_loss=avg_wall_loss,
            recommendations=recommendations
        )
