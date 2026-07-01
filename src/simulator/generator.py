import os
import time
import random
import logging
import datetime
import json
import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal, init_db
from src.database.models import Telemetry, Alert, Recommendation, ScenarioEvent
from src.analytics.change_detection import ChangeDetectionEngine
from src.analytics.policy_engine import RRMPolicyEngine
from src.realistic_simulator.scenario_engine import ScenarioEngine
from src.realistic_simulator.models import APState, ClientState
from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
from src.realistic_simulator.digital_twin import DigitalTwinManager

logger = logging.getLogger("RRM.Simulator")

class BackgroundSimulator:
    """
    Main background simulator worker.
    Generates telemetry for multiple Access Points, runs change detection,
    evaluates policies, and writes all records to the database.
    """
    def __init__(self):
        # Configure simulation parameters from environment
        self.interval = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", 60))
        self.speed_multiplier = float(os.getenv("SIMULATOR_SPEED_MULTIPLIER", 1.0))
        self.num_aps = int(os.getenv("NUMBER_OF_APS", 3))
        self.seed_historical = os.getenv("SEED_HISTORICAL_DATA", "true").lower() == "true"
        self.seed_hours = int(os.getenv("SEED_HOURS", 6))
        
        # New Simulation Mode configs
        self.simulator_mode = os.getenv("SIMULATOR_MODE", "demo").lower() # demo, auto, manual
        self.scenario_duration_seconds = int(os.getenv("SIMULATOR_SCENARIO_DURATION_SECONDS", 30))
        
        self.sim_tick = 0

        # Initialize analytical engines and Digital Twin
        self.change_detector = ChangeDetectionEngine()
        self.policy_engine = RRMPolicyEngine()
        self.digital_twin = DigitalTwinManager()

        # Define default AP configs
        self.ap_configs = [
            {"ap_id": f"AP_00{i+1}_Floor{1 if i<2 else 2}", "channel": 36 if i%2==0 else 6, "base_clients": 5 + i*7}
            for i in range(self.num_aps)
        ]
        
        # Keep track of simulation states per AP
        self.states = {}
        for config in self.ap_configs:
            self.states[config["ap_id"]] = {
                "channel": config["channel"],
                "base_clients": config["base_clients"],
                "ap_state": None,
                "clients": None,
                "scenario_idx": 0,
                "scenario_start_time": None,
                "current_scenario_name": "Normal Office",
                "manual_override": None,
                "active_scenario_event_id": None
            }

    def seed_data_if_empty(self) -> None:
        """Seeds the database with historical data if configured and the telemetry table is empty."""
        pass # Skipping legacy seed logic for clarity in the digital twin

    def step(self) -> None:
        """Runs a single real-time simulation step, inserting data into the database."""
        db: Session = SessionLocal()
        try:
            self.sim_tick += 1
            self._execute_simulation_step(db, datetime.datetime.utcnow())
        except Exception as e:
            logger.error(f"Error executing real-time simulation step: {e}")
            db.rollback()
        finally:
            db.close()

    def run_loop(self, stop_event=None) -> None:
        """Runs the continuous simulation loop until stopped or interrupted."""
        logger.info("Initializing database schemas before loop starts...")
        init_db()
        self.seed_data_if_empty()
        
        adjusted_interval = self.interval / self.speed_multiplier
        logger.info(f"Starting real-time simulation loop. Step interval: {self.interval}s (Mode: {self.simulator_mode})")
        
        while True:
            if stop_event and stop_event.is_set():
                logger.info("Stopping background simulation loop...")
                break
            
            start_time = time.time()
            self.step()
            
            elapsed = time.time() - start_time
            sleep_time = max(0.1, adjusted_interval - elapsed)
            time.sleep(sleep_time)

    def force_scenario(self, ap_id: str, scenario_name: str):
        """API hook to force a manual scenario."""
        if ap_id in self.states:
            self.states[ap_id]["manual_override"] = scenario_name

    def _execute_simulation_step(self, db: Session, timestamp: datetime.datetime) -> None:
        for ap_id, state in self.states.items():
            
            # --- Scenario Transition Logic ---
            if state["scenario_start_time"] is None:
                state["scenario_start_time"] = timestamp
            
            elapsed_seconds = (timestamp - state["scenario_start_time"]).total_seconds()
            transitioned = False
            
            if state["manual_override"]:
                if state["current_scenario_name"] != state["manual_override"]:
                    state["current_scenario_name"] = state["manual_override"]
                    transitioned = True
                # Clear override so it holds unless changed again
            elif elapsed_seconds >= self.scenario_duration_seconds:
                if self.simulator_mode == "demo":
                    state["scenario_idx"] = (state["scenario_idx"] + 1) % len(ScenarioEngine.SCENARIO_NAMES)
                    state["current_scenario_name"] = ScenarioEngine.SCENARIO_NAMES[state["scenario_idx"]]
                elif self.simulator_mode == "auto":
                    state["current_scenario_name"] = random.choice(ScenarioEngine.SCENARIO_NAMES)
                
                state["scenario_start_time"] = timestamp
                transitioned = True

            scenario = ScenarioEngine.get_scenario(state["current_scenario_name"])
            
            # --- Initialize Physics State ---
            if state["ap_state"] is None:
                state["ap_state"] = APState(ap_id=ap_id, channel=state["channel"], channel_width=40, base_noise=-95.0, x=random.uniform(0, 50), y=random.uniform(0, 50), freq_mhz=5180.0, tx_power_dbm=20.0, channel_capacity_mbps=300.0)
            
            # Reset clients if transition happened and override is required
            target_clients = state["base_clients"]
            if scenario.client_count_override:
                target_clients = random.randint(scenario.client_count_override[0], scenario.client_count_override[1])
                
            if state["clients"] is None or transitioned:
                # Spawn clients nearby AP
                state["clients"] = []
                for i in range(target_clients):
                    if scenario.client_distance_override:
                        # Spawn client at a distance roughly equal to override (e.g. in a ring)
                        angle = random.uniform(0, 2 * math.pi)
                        distance = scenario.client_distance_override * random.uniform(0.85, 1.15)
                        dx = distance * math.cos(angle)
                        dy = distance * math.sin(angle)
                    else:
                        # Normal office: spread clients between 2.0 and 15.0 meters
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.uniform(2.0, 15.0)
                        dx = distance * math.cos(angle)
                        dy = distance * math.sin(angle)
                        
                    # Wall count based on scenario or distance
                    if scenario.name == "Weak Signal Corner":
                        wall_count = random.randint(2, 4)
                    else:
                        if distance < 5.0:
                            wall_count = 0
                        elif distance < 10.0:
                            wall_count = random.randint(0, 1)
                        else:
                            wall_count = random.randint(1, 2)

                    client = ClientState(
                        client_id=f"{ap_id}_C{i}", 
                        x=state["ap_state"].x + dx, 
                        y=state["ap_state"].y + dy, 
                        demand_mbps=random.uniform(2.0, 15.0), 
                        wall_count=wall_count
                    )
                    state["clients"].append(client)
            
            # --- Sync to Digital Twin ---
            self.digital_twin.sync_ap(state["ap_state"])
            self.digital_twin.sync_clients(ap_id, state["clients"])
            
            # --- Generate Telemetry ---
            sim = TelemetrySimulator(state["ap_state"])
            record = sim.generate_telemetry(state["clients"], scenario=scenario)
            
            # --- Manage ScenarioEvent DB Record ---
            topology_json = json.dumps([{"id": c.client_id, "x": round(c.x, 2), "y": round(c.y, 2)} for c in state["clients"]])
            
            if transitioned or state["active_scenario_event_id"] is None:
                # Close old event
                if state["active_scenario_event_id"] is not None:
                    old_event = db.query(ScenarioEvent).filter(ScenarioEvent.id == state["active_scenario_event_id"]).first()
                    if old_event:
                        old_event.end_time = timestamp
                
                # Create new event
                new_event = ScenarioEvent(
                    ap_id=ap_id,
                    start_time=timestamp,
                    scenario_name=scenario.name,
                    root_cause=scenario.interference_type,
                    client_topology_snapshot=topology_json
                )
                db.add(new_event)
                db.flush()
                state["active_scenario_event_id"] = new_event.id
            
            # --- Calculate Topology Stats ---
            distances = []
            for c in state["clients"]:
                d = ((c.x - state["ap_state"].x)**2 + (c.y - state["ap_state"].y)**2)**0.5
                distances.append(d)
                
            max_dist = max(distances) if distances else 0.0
            min_dist = min(distances) if distances else 0.0

            # --- Save Telemetry ---
            telemetry_row = Telemetry(
                timestamp=timestamp,
                ap_id=ap_id,
                channel=state["channel"],
                rssi=round(record.rssi, 2),
                snr=round(record.snr, 2),
                noise_floor=round(record.noise_floor, 2),
                airtime_utilization=round(record.airtime_utilization / 100.0, 4),
                retry_rate=round(record.retry_rate, 4),
                client_count=record.client_count,
                qoe_score=record.qoe_score,
                qoe_category=record.qoe_category,
                interference_type=record.interference_type,
                distance=round(record.distance, 2),
                max_distance=round(max_dist, 2),
                closest_client=round(min_dist, 2),
                furthest_client=round(max_dist, 2),
                freq_mhz=record.freq_mhz,
                tx_power=record.tx_power,
                wall_count=record.wall_count,
                wall_loss=round(record.wall_loss, 2),
                scenario_name=scenario.name,
                path_loss_db=record.path_loss_db,
                estimated_rx_power_dbm=record.estimated_rx_power_dbm,
                sinr_db=record.sinr_db,
                mcs_index=record.mcs_index,
                phy_rate_mbps=record.phy_rate_mbps,
                latency_ms=record.latency_ms,
                throughput_mbps=record.throughput_mbps,
                spectrum_snapshot=json.dumps(record.sensing_report) if record.sensing_report else None
            )
            db.add(telemetry_row)
            db.flush()

            # --- Evaluate Change Detection (Alerts) ---
            history = (
                db.query(Telemetry)
                .filter(Telemetry.ap_id == ap_id)
                .order_by(Telemetry.timestamp.desc())
                .limit(40)
                .all()
            )
            history.reverse()
            
            import pandas as pd
            records = [{"timestamp": r.timestamp, "ap_id": r.ap_id, "retry_rate": r.retry_rate, "airtime_utilization": r.airtime_utilization, "noise_floor": r.noise_floor} for r in history]
            df = pd.DataFrame(records)
            new_alerts = self.change_detector.analyze_ap_telemetry(df)
            
            for alert_data in new_alerts:
                alert_obj = Alert(
                    timestamp=alert_data["timestamp"],
                    ap_id=alert_data["ap_id"],
                    alert_type=alert_data["alert_type"],
                    metric=alert_data["metric"],
                    value=alert_data["value"],
                    threshold=alert_data["threshold"],
                    description=f"[{scenario.name}] {alert_data['description']}"
                )
                db.add(alert_obj)

            # --- Evaluate Recommendations ---
            if record.recommendations:
                # Get the top ranked recommendation
                top_rec = sorted(record.recommendations, key=lambda x: x["confidence"], reverse=True)[0]
                
                # Update current event with triggered rec
                if state["active_scenario_event_id"]:
                    curr_event = db.query(ScenarioEvent).filter(ScenarioEvent.id == state["active_scenario_event_id"]).first()
                    if curr_event:
                        curr_event.recommendation_triggered = top_rec["action"]

                # Save all ranked recommendations
                for rec_data in record.recommendations:
                    rec_obj = Recommendation(
                        timestamp=timestamp,
                        ap_id=ap_id,
                        action=rec_data["action"],
                        current_value=str(state["channel"]),
                        recommended_value=str(state["channel"]), # placeholder
                        confidence=rec_data["confidence"],
                        root_cause=rec_data.get("root_cause", scenario.interference_type),
                        reason=rec_data["reason"],
                        expected_qoe_gain=rec_data.get("expected_qoe_gain", 0.0),
                        expected_retry_reduction=rec_data.get("expected_retry_reduction", 0.0)
                    )
                    db.add(rec_obj)
                    
                    if rec_data["action"] == "CHANNEL_CHANGE" and rec_data["confidence"] > 0.9:
                        state["channel"] = 36 if state["channel"] != 36 else 149

        db.commit()
