import os
import csv
import random
import datetime
import unittest
from typing import List, Dict, Any

class APSimulator:
    """
    Simulates a single WiFi Access Point (AP) and generates realistic,
    stateful time-series telemetry.
    """
    def __init__(self, ap_id: str, channel: int, base_clients: int = 10):
        self.ap_id = ap_id
        self.channel = channel
        self.base_clients = base_clients
        
        # Base state defaults
        self.base_noise_floor = -95.0  # dBm
        self.base_retry_rate = 0.03    # 3%
        self.base_airtime_util = 0.15  # 15%
        
        # State modifiers for simulating realistic fluctuations and occasional anomalies
        self.anomaly_state = "NORMAL"  # Can be NORMAL, INTERFERENCE, SURGE, or CONGESTED
        self.anomaly_ticks = 0

    def set_anomaly_state(self, state: str, ticks: int = 5) -> None:
        """Injects a specific network condition state for a duration of ticks."""
        self.anomaly_state = state
        self.anomaly_ticks = ticks

    def step(self) -> Dict[str, Any]:
        """
        Advances the AP simulation by one step (1 minute) and returns
        the simulated telemetry metrics.
        """
        # Decrement anomaly timer
        if self.anomaly_ticks > 0:
            self.anomaly_ticks -= 1
            if self.anomaly_ticks == 0:
                self.anomaly_state = "NORMAL"

        # Apply state modifiers based on current condition
        noise_mod = 0.0
        retry_mod = 0.0
        client_mod = 0
        airtime_mod = 0.0

        if self.anomaly_state == "INTERFERENCE":
            # Simulate radar or microwave interference: higher noise, higher retries
            noise_mod = random.uniform(10.0, 20.0)
            retry_mod = random.uniform(0.15, 0.35)
            airtime_mod = random.uniform(0.10, 0.25)
        elif self.anomaly_state == "SURGE":
            # Simulate a sudden influx of clients
            client_mod = random.randint(15, 30)
            retry_mod = random.uniform(0.02, 0.08)
            airtime_mod = random.uniform(0.20, 0.40)
        elif self.anomaly_state == "CONGESTED":
            # High channel utilization and high packet retransmissions
            retry_mod = random.uniform(0.12, 0.25)
            airtime_mod = random.uniform(0.45, 0.65)

        # Generate realistic metrics
        client_count = max(0, int(random.normalvariate(self.base_clients + client_mod, 2.0)))
        
        # Noise floor (typical range: -100 to -80 dBm)
        noise_floor = min(-70.0, max(-105.0, random.normalvariate(self.base_noise_floor + noise_mod, 1.5)))
        
        # Client average RSSI (typical range: -85 to -50 dBm)
        rssi = random.normalvariate(-65.0, 5.0) if client_count > 0 else -95.0
        
        # SNR = RSSI - Noise Floor (dB)
        snr = max(0.0, rssi - noise_floor) if client_count > 0 else 0.0
        
        # Retry rate (0.0 to 1.0)
        retry_rate = min(1.0, max(0.0, random.normalvariate(self.base_retry_rate + retry_mod, 0.01)))
        
        # Airtime utilization: driven by clients, retry rates, and environmental noise
        client_load = client_count * 0.025
        retry_load = retry_rate * 0.6
        airtime_util = min(0.98, max(0.02, random.normalvariate(self.base_airtime_util + client_load + retry_load + airtime_mod, 0.03)))

        return {
            "ap_id": self.ap_id,
            "channel": self.channel,
            "rssi": round(rssi, 2),
            "snr": round(snr, 2),
            "noise_floor": round(noise_floor, 2),
            "airtime_utilization": round(airtime_util, 4),
            "retry_rate": round(retry_rate, 4),
            "client_count": client_count
        }


class WiFiNetworkSimulator:
    """
    Orchestrates telemetry generation for multiple Access Points
    and handles saving output to a CSV file.
    """
    def __init__(self, ap_configs: List[Dict[str, Any]]):
        self.aps = [
            APSimulator(
                ap_id=cfg["ap_id"], 
                channel=cfg["channel"], 
                base_clients=cfg.get("base_clients", 10)
            )
            for cfg in ap_configs
        ]

    def generate_step(self, timestamp: datetime.datetime) -> List[Dict[str, Any]]:
        """Generates a list of telemetry dictionaries for all managed APs at the given timestamp."""
        step_data = []
        for ap in self.aps:
            metrics = ap.step()
            metrics["timestamp"] = timestamp.isoformat()
            step_data.append(metrics)
        return step_data

    def generate_history(self, output_path: str, duration_hours: int = 6) -> None:
        """
        Generates continuous historical telemetry over a period of time
        and writes it into a CSV file.
        """
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(hours=duration_hours)
        
        # Fields mapping CSV headers
        fieldnames = ["timestamp", "ap_id", "channel", "rssi", "snr", "noise_floor", "airtime_utilization", "retry_rate", "client_count"]

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Write data to CSV
        with open(output_path, mode="w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            current_time = start_time
            # Increment minute-by-minute
            while current_time <= now:
                # Randomly inject anomalies to make dataset rich
                for ap in self.aps:
                    if ap.anomaly_state == "NORMAL" and random.random() < 0.02:
                        state = random.choice(["INTERFERENCE", "SURGE", "CONGESTED"])
                        ap.set_anomaly_state(state, ticks=random.randint(5, 15))
                
                step_records = self.generate_step(current_time)
                for record in step_records:
                    writer.writerow(record)
                
                current_time += datetime.timedelta(minutes=1)


# ==========================================
# Unit Tests (Self-contained Suite)
# ==========================================

class TestAPSimulator(unittest.TestCase):
    """Unit tests verifying simulator functions and outputs."""
    
    def setUp(self):
        self.ap = APSimulator(ap_id="AP_TEST", channel=36, base_clients=10)

    def test_default_telemetry_bounds(self):
        """Verify normal telemetry metrics fall within valid physical bounds."""
        metrics = self.ap.step()
        self.assertEqual(metrics["ap_id"], "AP_TEST")
        self.assertEqual(metrics["channel"], 36)
        self.assertTrue(-100 <= metrics["rssi"] <= -30)
        self.assertTrue(metrics["snr"] >= 0)
        self.assertTrue(-110 <= metrics["noise_floor"] <= -60)
        self.assertTrue(0.0 <= metrics["airtime_utilization"] <= 1.0)
        self.assertTrue(0.0 <= metrics["retry_rate"] <= 1.0)
        self.assertTrue(metrics["client_count"] >= 0)

    def test_interference_anomaly_injection(self):
        """Verify that injecting an interference anomaly increases noise floor and retry rate."""
        self.ap.set_anomaly_state("INTERFERENCE", ticks=5)
        
        metrics = self.ap.step()
        self.assertEqual(self.ap.anomaly_state, "INTERFERENCE")
        self.assertEqual(self.ap.anomaly_ticks, 4)
        
        # Check that noise floor is higher than the baseline average (-95)
        self.assertTrue(metrics["noise_floor"] > -90)
        # Check that retry rate is significantly elevated
        self.assertTrue(metrics["retry_rate"] > 0.10)

    def test_surge_anomaly_injection(self):
        """Verify that client surge anomaly increases client count."""
        self.ap.set_anomaly_state("SURGE", ticks=3)
        metrics = self.ap.step()
        
        self.assertTrue(metrics["client_count"] > 15)


class TestWiFiNetworkSimulator(unittest.TestCase):
    """Unit tests verifying multi-AP orchestrator and CSV operations."""
    
    def test_network_generation(self):
        configs = [
            {"ap_id": "AP_1", "channel": 1, "base_clients": 5},
            {"ap_id": "AP_2", "channel": 11, "base_clients": 15}
        ]
        simulator = WiFiNetworkSimulator(configs)
        records = simulator.generate_step(datetime.datetime.now())
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["ap_id"], "AP_1")
        self.assertEqual(records[1]["ap_id"], "AP_2")

    def test_csv_file_generation(self):
        temp_csv = "temp_telemetry_test.csv"
        configs = [{"ap_id": "AP_1", "channel": 1, "base_clients": 5}]
        simulator = WiFiNetworkSimulator(configs)
        
        try:
            simulator.generate_history(temp_csv, duration_hours=1)
            self.assertTrue(os.path.exists(temp_csv))
            
            # Verify file contents
            with open(temp_csv, mode="r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # 1 hour simulation has 61 steps
                self.assertGreater(len(rows), 50)
                self.assertEqual(rows[0]["ap_id"], "AP_1")
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--run-simulation":
        # Example script execution:
        ap_setups = [
            {"ap_id": "AP_001_Floor1", "channel": 36, "base_clients": 12},
            {"ap_id": "AP_002_Floor1", "channel": 149, "base_clients": 8},
            {"ap_id": "AP_003_Floor2", "channel": 6, "base_clients": 20}
        ]
        sim = WiFiNetworkSimulator(ap_setups)
        csv_path = "telemetry_output.csv"
        print(f"Generating 6 hours of simulation data to: {csv_path}...")
        sim.generate_history(csv_path, duration_hours=6)
        print("Done!")
    else:
        # Default action: run tests
        print("Running simulator unit tests...")
        unittest.main()
