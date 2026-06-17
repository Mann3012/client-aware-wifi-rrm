import os
import sys
import datetime
import unittest
import pandas as pd

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import SessionLocal, init_db, Base, engine
from src.database.models import Telemetry, Alert, Recommendation
from src.analytics.change_detection import ChangeDetectionEngine
from src.analytics.policy_engine import RRMPolicyEngine

class TestRRMComponentIntegration(unittest.TestCase):
    """Integration and Unit checks for database, change detection, and policies."""
    
    @classmethod
    def setUpClass(cls):
        # Initialize DB (creates database tables)
        init_db()

    def setUp(self):
        # Open DB Session
        self.db = SessionLocal()
        # Clean test tables
        self.db.query(Telemetry).delete()
        self.db.query(Alert).delete()
        self.db.query(Recommendation).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_database_insert_and_retrieve(self):
        """Verify we can write and read Telemetry rows successfully."""
        time_now = datetime.datetime.utcnow()
        telemetry = Telemetry(
            timestamp=time_now,
            ap_id="AP_VAL_01",
            channel=6,
            rssi=-62.5,
            snr=31.2,
            noise_floor=-93.7,
            airtime_utilization=0.22,
            retry_rate=0.04,
            client_count=14
        )
        self.db.add(telemetry)
        self.db.commit()
        
        # Query back
        stored = self.db.query(Telemetry).filter(Telemetry.ap_id == "AP_VAL_01").first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.channel, 6)
        self.assertEqual(stored.client_count, 14)
        self.assertEqual(stored.rssi, -62.5)

    def test_change_detection_and_alerts(self):
        """Verify that change detection creates correct alert records on anomalous trends."""
        # Create 15 entries ending with a spike in retry rate (90% retry rate)
        now = datetime.datetime.utcnow()
        records = []
        for i in range(15):
            t_val = now - datetime.timedelta(minutes=15-i)
            retry = 0.02 if i < 14 else 0.90  # Spike on the 15th step
            
            tel = Telemetry(
                timestamp=t_val,
                ap_id="AP_TEST_ANOMALY",
                channel=36,
                rssi=-65.0,
                snr=25.0,
                noise_floor=-90.0,
                airtime_utilization=0.15,
                retry_rate=retry,
                client_count=5
            )
            self.db.add(tel)
            records.append(tel)
        self.db.commit()

        # Run detector on the added series
        history = (
            self.db.query(Telemetry)
            .filter(Telemetry.ap_id == "AP_TEST_ANOMALY")
            .order_by(Telemetry.timestamp.asc())
            .all()
        )
        
        df_data = pd.DataFrame([
            {
                "timestamp": r.timestamp,
                "ap_id": r.ap_id,
                "retry_rate": r.retry_rate,
                "airtime_utilization": r.airtime_utilization,
                "noise_floor": r.noise_floor
            }
            for r in history
        ])
        
        detector = ChangeDetectionEngine()
        alerts = detector.analyze_ap_telemetry(df_data)
        
        # Verify alert was generated for the retry spike
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["alert_type"], "retry_spike")
        self.assertEqual(alerts[0]["metric"], "retry_rate")

    def test_policy_engine_recommendation(self):
        """Verify the policy engine generates CHANNEL_CHANGE action under critical conditions."""
        # Simulated telemetry with high airtime and retry rate
        telemetry = {
            "ap_id": "AP_CONGESTED",
            "channel": 36,
            "rssi": -72.0,
            "snr": 18.0,
            "noise_floor": -90.0,
            "airtime_utilization": 0.85,  # Congested
            "retry_rate": 0.25,           # High packet retries
            "client_count": 22
        }
        
        # Matching active alerts
        active_alerts = [
            {"alert_type": "retry_spike", "metric": "retry_rate"},
            {"alert_type": "airtime_congestion", "metric": "airtime_utilization"}
        ]
        
        engine = RRMPolicyEngine()
        recommendation = engine.evaluate(telemetry, active_alerts)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation["action"], "CHANNEL_CHANGE")
        self.assertNotEqual(recommendation["recommended_value"], "36")
        self.assertTrue(recommendation["confidence"] >= 0.90)


if __name__ == "__main__":
    print("Running integration tests...")
    unittest.main()
