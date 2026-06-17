import os
import time
import random
import logging
import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal, init_db
from src.database.models import Telemetry, Alert, Recommendation
from src.analytics.change_detection import ChangeDetectionEngine
from src.analytics.policy_engine import RRMPolicyEngine

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
        self.simulator_mode = os.getenv("SIMULATOR_MODE", "realistic")
        self.sim_tick = 0

        # Initialize analytical engines
        self.change_detector = ChangeDetectionEngine()
        self.policy_engine = RRMPolicyEngine()

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
                "anomaly_state": "NORMAL",
                "anomaly_ticks": 0,
                "base_noise_floor": -95.0,
                "base_retry_rate": 0.03,
                "base_airtime_util": 0.15
            }

    def _get_local_wifi_stats(self) -> Dict[str, Any]:
        """
        Runs 'netsh wlan show interfaces' to query the laptop's live WiFi metrics.
        Returns a dict containing 'rssi', 'channel', 'ssid', and 'signal' if successful, or empty dict.
        """
        import subprocess
        import re
        import sys
        
        if sys.platform != "win32":
            return {}
            
        try:
            # Run command to query active wlan interfaces
            # 0x08000000 prevents a command window popup on Windows
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0
            )
            if result.returncode != 0:
                return {}
                
            output = result.stdout
            stats = {}
            
            # Match Rssi (e.g. "Rssi                   : -38")
            rssi_match = re.search(r"Rssi\s+:\s+(-?\d+)", output, re.IGNORECASE)
            if rssi_match:
                stats["rssi"] = float(rssi_match.group(1))
                
            # Match Channel (e.g. "Channel                : 6")
            channel_match = re.search(r"Channel\s+:\s+(\d+)", output, re.IGNORECASE)
            if channel_match:
                stats["channel"] = int(channel_match.group(1))

            # Match SSID
            ssid_match = re.search(r"SSID\s+:\s+(.+)", output, re.IGNORECASE)
            if ssid_match:
                stats["ssid"] = ssid_match.group(1).strip()
                
            # Match Signal Percentage
            signal_match = re.search(r"Signal\s+:\s+(\d+)%", output, re.IGNORECASE)
            if signal_match:
                stats["signal"] = int(signal_match.group(1))

            return stats
        except Exception as e:
            logger.warning(f"Failed to query local WiFi interfaces: {e}")
            return {}

    def seed_data_if_empty(self) -> None:
        """
        Seeds the database with historical data if configured and the telemetry table is empty.
        Runs analytics and policies chronologically on each step to ensure state consistency.
        """
        if not self.seed_historical:
            return

        db: Session = SessionLocal()
        try:
            self.sim_tick += 1
            # Check if telemetry already exists
            count = db.query(Telemetry).count()
            if count > 0:
                logger.info(f"Database already contains {count} telemetry entries. Skipping seed.")
                return

            logger.info(f"Seeding database with {self.seed_hours} hours of simulated historical data...")
            now = datetime.datetime.utcnow()
            start_time = now - datetime.timedelta(hours=self.seed_hours)
            
            current_time = start_time
            steps = int(self.seed_hours * 60)
            
            for step in range(steps):
                # Randomly inject anomalies during seeding
                for ap_id, state in self.states.items():
                    if state["anomaly_state"] == "NORMAL" and random.random() < 0.02:
                        state["anomaly_state"] = random.choice(["INTERFERENCE", "SURGE", "CONGESTED"])
                        state["anomaly_ticks"] = random.randint(5, 15)

                self._execute_simulation_step(db, current_time)
                current_time += datetime.timedelta(minutes=1)

            logger.info("Historical data seed completed successfully.")
        except Exception as e:
            logger.error(f"Error seeding historical data: {e}")
            db.rollback()
        finally:
            db.close()

    def step(self) -> None:
        """Runs a single real-time simulation step, inserting data into the database."""
        db: Session = SessionLocal()
        try:
            self.sim_tick += 1
            # Randomly trigger anomalies occasionally
            for ap_id, state in self.states.items():
                if state["anomaly_state"] == "NORMAL" and random.random() < 0.03:
                    state["anomaly_state"] = random.choice(["INTERFERENCE", "SURGE", "CONGESTED"])
                    state["anomaly_ticks"] = random.randint(5, 12)
                    logger.info(f"Injecting anomaly '{state['anomaly_state']}' on {ap_id} for {state['anomaly_ticks']} minutes.")

            # Run step
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
        logger.info(f"Starting real-time simulation loop. Step interval: {self.interval}s (Speed Multiplier: {self.speed_multiplier}x)")
        
        while True:
            if stop_event and stop_event.is_set():
                logger.info("Stopping background simulation loop...")
                break
            
            start_time = time.time()
            self.step()
            
            # Sleep adjusting for work execution time
            elapsed = time.time() - start_time
            sleep_time = max(0.1, adjusted_interval - elapsed)
            time.sleep(sleep_time)

    def _execute_simulation_step(self, db: Session, timestamp: datetime.datetime) -> None:
        """Generates telemetry, checks change detection, runs policies, and saves to database."""
        cycle_tick = self.sim_tick % 25
        
        active_event = None
        if 5 <= cycle_tick < 10:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("Microwave", noise_boost_db=15.0, airtime_boost_percent=0.0, duration_minutes=5, active=True)
        elif 15 <= cycle_tick < 20:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("BLE Congestion", noise_boost_db=3.0, airtime_boost_percent=5.0, duration_minutes=5, active=True)
        elif 20 <= cycle_tick < 25:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("Neighbor AP Congestion", noise_boost_db=0.0, airtime_boost_percent=20.0, duration_minutes=5, active=True)

        for ap_id, state in self.states.items():
            if self.simulator_mode == "realistic":
                from src.realistic_simulator.models import APState, ClientState
                from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
                ap_state = APState(ap_id=ap_id, channel=state["channel"], channel_width=40, base_noise=-95.0)
                sim = TelemetrySimulator(ap_state)
                clients = [
                    ClientState(client_id=f"{ap_id}_C1", distance_meters=5.0, demand_mbps=10.0),
                    ClientState(client_id=f"{ap_id}_C2", distance_meters=15.0, demand_mbps=20.0),
                    ClientState(client_id=f"{ap_id}_C3", distance_meters=20.0, demand_mbps=30.0),
                ]
                record = sim.generate_telemetry(clients, event=active_event)
                
                rssi = record.rssi
                noise_floor = record.noise_floor
                snr = record.snr
                airtime_util = record.airtime_utilization / 100.0
                retry_rate = record.retry_rate
                client_count = record.client_count
                qoe_score = record.qoe_score
                qoe_category = record.qoe_category
                interference_type = active_event.event_type if active_event else "None"
                
            else:
                if state["anomaly_ticks"] > 0:
                    state["anomaly_ticks"] -= 1
                    if state["anomaly_ticks"] == 0:
                        state["anomaly_state"] = "NORMAL"

                noise_mod = 0.0
                retry_mod = 0.0
                client_mod = 0
                airtime_mod = 0.0

                if state["anomaly_state"] == "INTERFERENCE":
                    noise_mod = random.uniform(12.0, 22.0)
                    retry_mod = random.uniform(0.15, 0.35)
                    airtime_mod = random.uniform(0.05, 0.15)
                elif state["anomaly_state"] == "SURGE":
                    client_mod = random.randint(15, 30)
                    retry_mod = random.uniform(0.01, 0.05)
                    airtime_mod = random.uniform(0.20, 0.40)
                elif state["anomaly_state"] == "CONGESTED":
                    retry_mod = random.uniform(0.10, 0.22)
                    airtime_mod = random.uniform(0.40, 0.65)

                local_stats = {}
                if ap_id == "AP_001_Floor1":
                    local_stats = self._get_local_wifi_stats()

                client_count = max(0, int(random.normalvariate(state["base_clients"] + client_mod, 2.0)))
                noise_floor = min(-70.0, max(-105.0, random.normalvariate(state["base_noise_floor"] + noise_mod, 1.5)))
                
                if local_stats and "rssi" in local_stats:
                    rssi = local_stats["rssi"]
                    if "channel" in local_stats:
                        state["channel"] = local_stats["channel"]
                else:
                    rssi = random.normalvariate(-65.0, 4.0) if client_count > 0 else -95.0

                snr = max(0.0, rssi - noise_floor) if client_count > 0 else 0.0
                retry_rate = min(1.0, max(0.0, random.normalvariate(state["base_retry_rate"] + retry_mod, 0.01)))
                
                client_load = client_count * 0.02
                retry_load = retry_rate * 0.5
                airtime_util = min(0.98, max(0.02, random.normalvariate(state["base_airtime_util"] + client_load + retry_load + airtime_mod, 0.03)))
                qoe_score = None
                qoe_category = None
                interference_type = "None"

            telemetry_row = Telemetry(
                timestamp=timestamp,
                ap_id=ap_id,
                channel=state["channel"],
                rssi=round(rssi, 2),
                snr=round(snr, 2),
                noise_floor=round(noise_floor, 2),
                airtime_utilization=round(airtime_util, 4),
                retry_rate=round(retry_rate, 4),
                client_count=client_count,
                qoe_score=qoe_score,
                qoe_category=qoe_category,
                interference_type=interference_type
            )
            db.add(telemetry_row)
            db.flush() # Flushes to database to allow query calculations

            # 3. Retrieve historical slice for Change Detection
            # We need the last ~40 minutes of telemetry to compute EWMA/CUSUM
            # Note: Fetching from DB handles sorting and ensures accurate calculations
            history = (
                db.query(Telemetry)
                .filter(Telemetry.ap_id == ap_id)
                .order_by(Telemetry.timestamp.desc())
                .limit(40)
                .all()
            )
            history.reverse() # Sort chronologically for detectors

            # Convert DB objects to DataFrame for Change Detection Engine
            records = [
                {
                    "timestamp": r.timestamp,
                    "ap_id": r.ap_id,
                    "retry_rate": r.retry_rate,
                    "airtime_utilization": r.airtime_utilization,
                    "noise_floor": r.noise_floor
                }
                for r in history
            ]
            df = pd_from_records_fallback(records)

            # Run Change Detection
            new_alerts = self.change_detector.analyze_ap_telemetry(df)
            
            # Save Alerts
            alert_db_objects = []
            for alert_data in new_alerts:
                alert_obj = Alert(
                    timestamp=alert_data["timestamp"],
                    ap_id=alert_data["ap_id"],
                    alert_type=alert_data["alert_type"],
                    metric=alert_data["metric"],
                    value=alert_data["value"],
                    threshold=alert_data["threshold"],
                    description=alert_data["description"]
                )
                db.add(alert_obj)
                alert_db_objects.append(alert_data)

            # 4. Evaluate Policy recommendations
            telemetry_dict = {
                "ap_id": ap_id,
                "channel": state["channel"],
                "rssi": rssi,
                "snr": snr,
                "noise_floor": noise_floor,
                "airtime_utilization": airtime_util,
                "retry_rate": retry_rate,
                "client_count": client_count
            }

            rec_data = self.policy_engine.evaluate(telemetry_dict, alert_db_objects)
            if rec_data:
                # Save recommendation
                rec_obj = Recommendation(
                    timestamp=timestamp,
                    ap_id=rec_data["ap_id"],
                    action=rec_data["action"],
                    current_value=rec_data["current_value"],
                    recommended_value=rec_data["recommended_value"],
                    confidence=rec_data["confidence"],
                    reason=rec_data["reason"]
                )
                db.add(rec_obj)

                # In real network: apply channel change in our internal simulator state
                if rec_data["action"] == "CHANNEL_CHANGE":
                    state["channel"] = int(rec_data["recommended_value"])
                    logger.info(f"Applying recommended Channel Change for {ap_id} to Channel {state['channel']}")

        db.commit()


def pd_from_records_fallback(records: List[Dict[str, Any]]):
    """Fallback helper to generate a pandas DataFrame."""
    import pandas as pd
    return pd.DataFrame(records)
