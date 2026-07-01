import unittest
from src.realistic_simulator.recommendation_engine import DiagnosticEngine

class TestDiagnosticEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DiagnosticEngine()

    def test_weak_signal_fallback(self):
        # RSSI ≈ -61, retries ≈ 25%, QoE ≈ 72 should NOT return "Healthy"
        diagnoses = self.engine.diagnose(
            path_loss_db=70.0,
            interference_type="None",
            noise_floor=-95.0,
            retry_rate=0.25,
            qoe_score=72.0,
            airtime_utilization=0.4,
            client_count=5,
            rssi=-61.0
        )
        self.assertTrue(len(diagnoses) > 0)
        self.assertNotEqual(diagnoses[0].root_cause, "Healthy")
        
    def test_score_all_rule(self):
        # Trigger multiple conditions to ensure it's not just first match
        diagnoses = self.engine.diagnose(
            path_loss_db=95.0, # Coverage
            interference_type="MICROWAVE",
            noise_floor=-80.0, # Microwave
            retry_rate=0.30,
            qoe_score=50.0,
            airtime_utilization=80.0, # Congestion
            client_count=30, # Congestion
            rssi=-80.0
        )
        self.assertTrue(len(diagnoses) >= 3)
        root_causes = [d.root_cause for d in diagnoses]
        self.assertIn("Coverage Problem", root_causes)
        self.assertIn("Client Congestion", root_causes)
        self.assertIn("Microwave Interference", root_causes)

    def test_confidence_scaling(self):
        d1 = self.engine.diagnose(path_loss_db=92.0, interference_type="None", noise_floor=-95.0, retry_rate=0.01, qoe_score=90.0, airtime_utilization=0.1, client_count=1, rssi=-60.0)
        d2 = self.engine.diagnose(path_loss_db=100.0, interference_type="None", noise_floor=-95.0, retry_rate=0.01, qoe_score=90.0, airtime_utilization=0.1, client_count=1, rssi=-60.0)
        
        c1 = [d for d in d1 if d.root_cause == "Coverage Problem"][0]
        c2 = [d for d in d2 if d.root_cause == "Coverage Problem"][0]
        
        self.assertTrue(c2.confidence > c1.confidence)

    def test_dynamic_impact(self):
        d1 = self.engine.diagnose(path_loss_db=95.0, interference_type="None", noise_floor=-95.0, retry_rate=0.10, qoe_score=70.0, airtime_utilization=0.1, client_count=1, rssi=-60.0)
        d2 = self.engine.diagnose(path_loss_db=95.0, interference_type="None", noise_floor=-95.0, retry_rate=0.30, qoe_score=50.0, airtime_utilization=0.1, client_count=1, rssi=-60.0)
        
        c1 = [d for d in d1 if d.root_cause == "Coverage Problem"][0]
        c2 = [d for d in d2 if d.root_cause == "Coverage Problem"][0]
        
        self.assertTrue(c2.expected_qoe_gain > c1.expected_qoe_gain)
        self.assertTrue(c2.expected_retry_reduction > c1.expected_retry_reduction)

if __name__ == "__main__":
    unittest.main()
