import os
import sys
import unittest
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import SessionLocal, init_db
from src.database.models import Telemetry, Recommendation
from src.realistic_simulator.models import APState, ClientState
from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
from src.realistic_simulator.scenario_engine import ScenarioEngine
from src.api.routes import get_telemetry, get_recommendations

class TestRRMSystemE2EPipeline(unittest.TestCase):
    """End-to-End Pipeline test validating Simulator -> Database -> REST API data flow."""

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = SessionLocal()
        self.db.query(Telemetry).delete()
        self.db.query(Recommendation).delete()
        self.db.commit()

        # Set up a test AP and Client
        self.ap = APState(
            ap_id="AP_E2E_01",
            channel=36,
            channel_width=40,
            tx_power_dbm=20.0,
            x=0.0,
            y=0.0,
            freq_mhz=5180.0
        )
        self.clients = [
            ClientState(client_id="Client_E2E_01", demand_mbps=10.0, x=15.0, y=0.0, wall_count=2)
        ]
        self.simulator = TelemetrySimulator(self.ap)

    def tearDown(self):
        self.db.close()

    def test_microwave_burst_flow(self):
        """Verifies full E2E flow for the 'Microwave Burst' scenario."""
        scenario = ScenarioEngine.get_scenario("Microwave Burst")
        
        # 1. Run Simulator to generate Telemetry & Recommendation
        sim_record = self.simulator.generate_telemetry(self.clients, scenario)
        
        # 2. Write to Database
        db_telemetry = Telemetry(
            timestamp=datetime.datetime.utcnow(),
            ap_id=sim_record.ap_id,
            channel=sim_record.channel,
            rssi=sim_record.rssi,
            snr=sim_record.snr,
            noise_floor=sim_record.noise_floor,
            airtime_utilization=sim_record.airtime_utilization,
            retry_rate=sim_record.retry_rate,
            client_count=sim_record.client_count,
            qoe_score=sim_record.qoe_score,
            qoe_category=sim_record.qoe_category,
            interference_type=sim_record.interference_type,
            distance=sim_record.distance,
            max_distance=sim_record.distance,
            closest_client=sim_record.distance,
            furthest_client=sim_record.distance,
            freq_mhz=sim_record.freq_mhz,
            tx_power=sim_record.tx_power,
            wall_count=sim_record.wall_count,
            wall_loss=sim_record.wall_loss,
            scenario_name=scenario.name,
            path_loss_db=sim_record.path_loss_db,
            estimated_rx_power_dbm=sim_record.estimated_rx_power_dbm,
            sinr_db=sim_record.sinr_db,
            mcs_index=sim_record.mcs_index,
            phy_rate_mbps=sim_record.phy_rate_mbps,
            latency_ms=sim_record.latency_ms,
            throughput_mbps=sim_record.throughput_mbps
        )
        self.db.add(db_telemetry)
        self.db.commit()

        # Write recommendations
        for rec in sim_record.recommendations:
            db_rec = Recommendation(
                timestamp=datetime.datetime.utcnow(),
                ap_id=sim_record.ap_id,
                action=rec["action"],
                recommended_value=rec.get("recommended_value", str(self.ap.channel)),
                current_value=rec.get("current_value", str(self.ap.channel)),
                confidence=rec["confidence"],
                root_cause=rec.get("root_cause", "MICROWAVE_BURST"),
                reason=rec["reason"],
                expected_qoe_gain=rec.get("expected_qoe_gain", 0.0)
            )
            self.db.add(db_rec)
        self.db.commit()

        # 3. Retrieve through REST API router functions directly
        telemetry_api = get_telemetry(ap_id="AP_E2E_01", limit=10, db=self.db)
        recs_api = get_recommendations(ap_id="AP_E2E_01", limit=10, db=self.db)

        # 4. Assert correctness
        self.assertEqual(telemetry_api[0].ap_id, "AP_E2E_01")
        self.assertEqual(telemetry_api[0].interference_type, "MICROWAVE")
        self.assertEqual(telemetry_api[0].scenario_name, "Microwave Burst")
        
        self.assertTrue(len(recs_api) > 0)
        self.assertEqual(recs_api[0].action, "CHANNEL_CHANGE")
        self.assertEqual(recs_api[0].root_cause, "MICROWAVE")

    def test_pipeline_field_consistency(self):
        """
        Verifies that per-link physics metrics flow end-to-end without loss
        or silent derivation in the presentation layer.
        """
        scenario = ScenarioEngine.get_scenario("Normal Office")
        
        # 1. Generate
        sim_record = self.simulator.generate_telemetry(self.clients, scenario)
        
        # 2. Persist
        db_telemetry = Telemetry(
            timestamp=datetime.datetime.utcnow(),
            ap_id=sim_record.ap_id,
            channel=sim_record.channel,
            rssi=sim_record.rssi,
            snr=sim_record.snr,
            noise_floor=sim_record.noise_floor,
            airtime_utilization=sim_record.airtime_utilization,
            retry_rate=sim_record.retry_rate,
            client_count=sim_record.client_count,
            path_loss_db=sim_record.path_loss_db,
            estimated_rx_power_dbm=sim_record.estimated_rx_power_dbm,
            sinr_db=sim_record.sinr_db,
            mcs_index=sim_record.mcs_index,
            phy_rate_mbps=sim_record.phy_rate_mbps,
            latency_ms=sim_record.latency_ms,
            throughput_mbps=sim_record.throughput_mbps
        )
        self.db.add(db_telemetry)
        self.db.commit()

        # 3. Retrieve
        telemetry_api = get_telemetry(ap_id="AP_E2E_01", limit=1, db=self.db)
        
        # 4. Verify fields exist and match exactly (Pipeline Invariant)
        api_record = telemetry_api[0]
        
        self.assertIsNotNone(api_record.path_loss_db)
        self.assertIsNotNone(api_record.estimated_rx_power_dbm)
        self.assertIsNotNone(api_record.sinr_db)
        self.assertIsNotNone(api_record.latency_ms)
        self.assertIsNotNone(api_record.throughput_mbps)
        
        # Values should be identical
        self.assertEqual(api_record.path_loss_db, sim_record.path_loss_db)
        self.assertEqual(api_record.latency_ms, sim_record.latency_ms)
        self.assertEqual(api_record.throughput_mbps, sim_record.throughput_mbps)

if __name__ == "__main__":
    unittest.main()
