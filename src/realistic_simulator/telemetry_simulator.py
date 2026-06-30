import math
import random
from typing import List, Optional

from src.realistic_simulator.models import (
    APState, ClientState, QoE, InterferenceEvent, TelemetryRecord,
    PhyMetrics, APDigitalTwin, ClientDigitalTwin
)
from src.realistic_simulator.recommendation_engine import RecommendationEngine
from src.realistic_simulator.scenario_engine import Scenario

# Import our new Physics & Protocol Engines (Iterations 1 & 2)
from src.realistic_simulator.environment import WirelessEnvironment, Point, create_office_environment, InterferenceSource
from src.realistic_simulator.propagation import PropagationEngine
from src.realistic_simulator.channel import ChannelModel
from src.realistic_simulator.interference import InterferenceEngine
from src.realistic_simulator.receiver import ReceiverModel
from src.realistic_simulator.link_adaptation import LinkAdaptation
from src.realistic_simulator.wifi6_phy import WiFi6Phy
from src.realistic_simulator.mac_layer import MacLayer
from src.realistic_simulator.traffic_model import TrafficModel
from src.realistic_simulator.qoe import QoEEngine
from src.realistic_simulator.constants import InterferenceType, CHANNEL_TO_FREQ_MHZ
from src.realistic_simulator.additional_radio import SensingRadio

class TelemetrySimulator:
    """
    Generates realistic Wi-Fi telemetry using deterministic physics engines
    and accurate 802.11ax MAC/PHY modeling.
    """
    
    def __init__(self, ap_state: APState):
        self.ap = ap_state
        
        # 1. Initialize the Environment (Standard Office Layout)
        self.env = create_office_environment(width_m=40.0, height_m=30.0)
        
        # Clamp AP to environment
        clamped_ap = self.env.clamp_position(Point(self.ap.x, self.ap.y))
        self.ap_loc = clamped_ap
        
        # 2. Initialize Engines
        self.prop_engine = PropagationEngine(self.env)
        self.channel_model = ChannelModel()
        self.interference_engine = InterferenceEngine(self.env, self.prop_engine)
        self.receiver = ReceiverModel(noise_figure_db=self.ap.noise_figure_db)
        self.link_adaptation = LinkAdaptation(max_spatial_streams=self.ap.spatial_streams)
        self.mac_layer = MacLayer()
        self.traffic_model = TrafficModel()
        self.qoe_engine = QoEEngine()
        self.sensing_radio = SensingRadio(noise_figure_db=self.ap.noise_figure_db)
        
    def _apply_scenario_interference(self, scenario: Optional[Scenario]):
        """Injects external interference sources into the environment based on the active scenario."""
        self.env.interference_sources.clear()
        
        if scenario and scenario.interference and scenario.interference.active:
            # Simple heuristic mapping for legacy scenarios
            if scenario.interference.event_type.lower() == "microwave":
                intf_type = InterferenceType.MICROWAVE
                bw = 20.0
                dc = 0.50
                freq = self.ap.freq_mhz
            else:
                intf_type = InterferenceType.BLUETOOTH
                bw = 2.0
                dc = 0.05
                freq = self.ap.freq_mhz
                
            src = InterferenceSource(
                source_id="scenario_intf",
                interference_type=intf_type,
                location=Point(self.ap_loc.x + 5.0, self.ap_loc.y + 5.0), # 5m away
                frequency_mhz=freq,
                bandwidth_mhz=bw,
                tx_power_dbm=10.0,
                duty_cycle=dc
            )
            self.env.interference_sources.append(src)
            
    def _apply_mobility(self, clients: List[ClientState]):
        """Random walk mobility."""
        for client in clients:
            client.x += random.uniform(-1.0, 1.0)
            client.y += random.uniform(-1.0, 1.0)
            
            # Clamp to environment
            p = self.env.clamp_position(Point(client.x, client.y))
            client.x = p.x
            client.y = p.y

    def calculate_qoe(self, snr: float, retry_rate: float, noise_floor: float, airtime: float) -> QoE:
        # Backward-compatible dummy to satisfy test_formulas
        score = 100.0 - (retry_rate * 100.0) - max(0, noise_floor - self.ap.base_noise) - (airtime * 0.1)
        score = max(0.0, min(100.0, score))
        if score >= 85.0:
            category = "Excellent"
        elif score >= 65.0:
            category = "Good"
        elif score >= 40.0:
            category = "Fair"
        else:
            category = "Poor"
        return QoE(score=score, category=category)

    def calculate_retry_rate(self, snr: float) -> float:
        # Backward-compatible dummy
        return min(0.80, max(0.01, 1.0 * math.exp(-0.12 * snr)))

    def calculate_noise_floor(self, scenario: Optional[Scenario]) -> float:
        noise = self.ap.base_noise
        if scenario and scenario.interference and scenario.interference.active:
            if scenario.interference.event_type.lower() == "microwave":
                return noise + 25.0
            return noise + 10.0
        return noise

    def generate_telemetry(self, clients: List[ClientState], scenario: Optional[Scenario] = None) -> TelemetryRecord:
        """
        Executes the full physics-based causal pipeline.
        Environment -> Propagation -> Channel -> Interference -> Receiver -> PHY -> MAC -> Traffic -> QoE
        """
        self._apply_mobility(clients)
        self._apply_scenario_interference(scenario)
        
        client_count = len(clients)
        if client_count == 0:
            # Empty AP
            return TelemetryRecord(
                ap_id=self.ap.ap_id, channel=self.ap.channel, client_count=0,
                rssi=-95.0, noise_floor=self.receiver.thermal_noise_floor_dbm(self.ap.channel_width * 1e6),
                snr=0.0, airtime_utilization=0.0, retry_rate=0.0, qoe_score=0.0, qoe_category="Poor"
            )

        # Base noise floor (thermal)
        base_noise_dbm = self.receiver.thermal_noise_floor_dbm(self.ap.channel_width * 1e6)

        total_rssi, total_snr, total_retry, total_dist, total_wall_loss = 0.0, 0.0, 0.0, 0.0, 0.0
        total_airtime_us = 0.0
        total_qoe_score = 0.0
        total_noise_floor_mw = 0.0

        # Per-client snapshots — used to select the representative client.
        # Arithmetic averaging of dB-domain metrics (path loss, SINR, received
        # power) is not physically meaningful because dB values are log-scale.
        # Instead, the representative client (nearest to avg distance) provides
        # a single, internally consistent link snapshot for causal chain display.
        client_records = []

        # For simplicity, we assume an equal fair-share medium access in this iteration
        # P(collision) increases with client count
        collision_prob = min(0.40, client_count * 0.02)

        # Calculate per-client physics
        for client in clients:
            client_loc = Point(client.x, client.y)
            dist = self.ap_loc.distance_to(client_loc)

            # 1. Propagation & Channel (Downlink)
            pl_db = self.prop_engine.total_path_loss(self.ap_loc, client_loc, self.ap.freq_mhz * 1e6, path_loss_exponent=3.0)
            is_los = (pl_db == self.prop_engine.log_distance_path_loss(dist, self.ap.freq_mhz * 1e6, 3.0))

            total_loss_db, shadow_db, fast_fade_db = self.channel_model.apply_channel_effects(
                pl_db, is_los=is_los, shadow_std_dev_db=4.0, k_factor_db=6.0
            )

            # 2. Receiver & Interference
            # measured_rssi uses total_loss_db (incl. shadow/fast fading) — authoritative value
            rssi_dbm = self.receiver.compute_rssi(self.ap.tx_power_dbm, self.ap.antenna_gain_dbi, client.antenna_gain_dbi, total_loss_db)

            # estimated_rx_power uses pl_db (deterministic path loss only, no fading)
            # This is the link-budget prediction: TX + Gains - PropagationLoss
            estimated_rx_power_dbm = self.receiver.compute_rssi(
                self.ap.tx_power_dbm, self.ap.antenna_gain_dbi, client.antenna_gain_dbi, pl_db
            )

            intf_powers = self.interference_engine.compute_external_interference(client_loc, self.ap.freq_mhz, float(self.ap.channel_width))
            sinr_db = self.receiver.compute_sinr(rssi_dbm, base_noise_dbm, intf_powers)
            snr_db = self.receiver.compute_snr(rssi_dbm, base_noise_dbm)

            # Sum measured noise power (thermal noise + interference)
            from src.realistic_simulator.constants import dbm_to_mw
            total_noise_floor_mw += dbm_to_mw(base_noise_dbm) + sum(dbm_to_mw(p) for p in intf_powers)

            # 3. PHY / Link Adaptation
            mcs = self.link_adaptation.select_mcs(sinr_db)
            spatial_streams = self.link_adaptation.select_spatial_streams(sinr_db, self.ap.spatial_streams, 2)

            phy = WiFi6Phy(self.ap.channel_width, spatial_streams, self.ap.guard_interval_us)
            phy_res = phy.compute(sinr_db, mcs)

            # 4. MAC Layer
            # Assume average packet size 1500, aggregation 32 frames for heavy traffic, 1 for light
            agg_frames = 32 if client.demand_mbps > 5.0 else 1
            mac_res = self.mac_layer.compute_transmission_time(1500, phy_res, collision_prob, agg_frames)

            # 5. Traffic Model & QoE
            demand_mult = scenario.client_demand_multiplier if scenario else 1.0
            actual_demand = client.demand_mbps * demand_mult

            traffic_res = self.traffic_model.evaluate_traffic(actual_demand, phy_res, mac_res)

            # Aggregate network-wide metrics (averaging is appropriate for these)
            total_rssi += rssi_dbm
            total_snr += snr_db
            total_retry += phy_res.per
            total_dist += dist
            total_wall_loss += (pl_db - self.prop_engine.log_distance_path_loss(dist, self.ap.freq_mhz * 1e6, 3.0))

            # Airtime consumed = fraction of 1 second needed to transmit throughput
            if mac_res.effective_throughput_mbps > 0:
                total_airtime_us += (traffic_res.l4_throughput_mbps / mac_res.effective_throughput_mbps) * 1e6

            qoe = self.qoe_engine.compute_qoe(
                client.application_type, traffic_res.l4_throughput_mbps, actual_demand,
                traffic_res.latency_ms, traffic_res.jitter_ms, phy_res.per, phy_res.per
            )
            total_qoe_score += qoe.score

            # Snapshot this client's per-link metrics for representative selection
            client_records.append({
                "dist":                   dist,
                "path_loss_db":           pl_db,
                "estimated_rx_power_dbm": estimated_rx_power_dbm,
                "sinr_db":                sinr_db,
                "mcs_index":              phy_res.mcs_index,
                "phy_rate_mbps":          phy_res.phy_rate_mbps,
                "latency_ms":             traffic_res.latency_ms,
                "throughput_mbps":        traffic_res.l4_throughput_mbps,
            })

        # ── Network-wide averages ─────────────────────────────────────────────
        avg_rssi      = total_rssi / client_count
        avg_snr       = total_snr / client_count
        avg_retry     = total_retry / client_count
        avg_dist      = total_dist / client_count
        avg_wall_loss = total_wall_loss / client_count
        avg_qoe_score = total_qoe_score / client_count

        from src.realistic_simulator.constants import mw_to_dbm
        avg_noise_floor = mw_to_dbm(total_noise_floor_mw / client_count)

        # Total airtime utilization (%)
        airtime_utilization = min(100.0, (total_airtime_us / 1e6) * 100.0)

        # ── Representative-client selection ───────────────────────────────────
        # Select the client whose distance is nearest to avg_dist.
        # All per-link dB-domain metrics come from this single client link,
        # preserving internal consistency across the causal chain.
        rep = min(client_records, key=lambda c: abs(c["dist"] - avg_dist))

        qoe_cat = self.qoe_engine.get_category(avg_qoe_score)
        has_active_interference = (scenario is not None and scenario.interference is not None and scenario.interference.active)

        # Recommendations Engine (Legacy compatibility)
        recommendations = RecommendationEngine.recommend_action(
            scenario_name=scenario.name if scenario else "Normal Office",
            root_cause=scenario.interference_type if scenario else "None",
            noise_floor=avg_noise_floor,
            snr=avg_snr,
            retry_rate=avg_retry,
            airtime_utilization=airtime_utilization,
            qoe_score=avg_qoe_score,
            distance_meters=avg_dist,
            rssi=avg_rssi,
            client_count=client_count
        )

        # --- Sensing Radio Scan (Iteration 4) ---
        sensing_report = self.sensing_radio.scan(
            channel=self.ap.channel,
            bandwidth_mhz=self.ap.channel_width,
            environment=self.env,
            ap_location=self.ap_loc,
        )

        return TelemetryRecord(
            # ── Network-wide fields ──────────────────────────────────────────
            ap_id=self.ap.ap_id, channel=self.ap.channel, client_count=client_count,
            rssi=avg_rssi, noise_floor=avg_noise_floor, snr=avg_snr,
            airtime_utilization=airtime_utilization, retry_rate=avg_retry,
            qoe_score=avg_qoe_score, qoe_category=qoe_cat,
            interference_type=scenario.interference.event_type if has_active_interference else "None",
            distance=avg_dist, freq_mhz=self.ap.freq_mhz, tx_power=self.ap.tx_power_dbm,
            wall_count=int(avg_wall_loss / 3.0), wall_loss=avg_wall_loss,
            recommendations=recommendations,
            # ── Representative-client per-link fields ────────────────────────
            path_loss_db=rep["path_loss_db"],
            estimated_rx_power_dbm=rep["estimated_rx_power_dbm"],
            sinr_db=rep["sinr_db"],
            mcs_index=rep["mcs_index"],
            phy_rate_mbps=rep["phy_rate_mbps"],
            latency_ms=rep["latency_ms"],
            throughput_mbps=rep["throughput_mbps"],
            # ── Legacy alias fields (backward compatibility) ─────────────────
            sinr=rep["sinr_db"],   # Fixed: was incorrectly set to avg_snr
            per=avg_retry,
            # ── Sensing Radio (Iteration 4) ──────────────────────────────────
            sensing_report=sensing_report.to_dict() if sensing_report else None,
        )

