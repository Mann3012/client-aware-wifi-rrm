import pytest
from src.realistic_simulator.models import APState, ClientState
from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
from src.realistic_simulator.scenario_engine import ScenarioEngine

def test_telemetry_generation():
    # Setup AP and Client
    ap = APState(ap_id="TEST_AP", channel=36, channel_width=40, tx_power_dbm=20.0, x=10.0, y=10.0, freq_mhz=5180.0)
    client1 = ClientState(client_id="C1", demand_mbps=5.0, x=12.0, y=10.0, application_type="voice")
    client2 = ClientState(client_id="C2", demand_mbps=15.0, x=30.0, y=25.0, application_type="video")
    
    sim = TelemetrySimulator(ap)
    scenario = ScenarioEngine.get_scenario("Normal Office")
    
    # Generate
    record = sim.generate_telemetry([client1, client2], scenario)
    
    assert record.ap_id == "TEST_AP"
    assert record.client_count == 2
    
    # Check physics bounds
    assert -100.0 <= record.rssi <= -20.0
    assert 0.0 <= record.snr <= 60.0
    assert 0.0 <= record.retry_rate <= 1.0
    assert 0.0 <= record.airtime_utilization <= 100.0
    
    # Verify that the new PHY fields we injected actually flowed through
    assert record.sinr is not None
    assert record.per is not None
    assert 0.0 <= record.qoe_score <= 100.0
    assert record.qoe_category in ["Excellent", "Good", "Fair", "Poor"]
