import os
import sys
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.realistic_simulator.models import APState, ClientState
from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
from src.realistic_simulator.scenario_engine import ScenarioEngine

def test_formulas():
    ap = APState(ap_id="TEST", channel=36, channel_width=40, base_noise=-95.0, x=0.0, y=0.0, tx_power_dbm=20.0, freq_mhz=5180.0)
    sim = TelemetrySimulator(ap)
    
    client = ClientState(client_id="C1", x=0.0, y=5.0, demand_mbps=10.0, wall_count=0) # distance = 5m
    
    record = sim.generate_telemetry([client], scenario=ScenarioEngine.get_scenario("Normal Office"))
    
    # 1. Assert SNR = RSSI - Noise
    assert math.isclose(record.snr, record.rssi - record.noise_floor, abs_tol=0.1), f"Expected SNR {record.rssi - record.noise_floor}, got {record.snr}"
    
    # 2. Assert RSSI drops with distance
    client_far = ClientState(client_id="C1", x=0.0, y=20.0, demand_mbps=10.0, wall_count=0) # distance = 20m
    record_far = sim.generate_telemetry([client_far], scenario=ScenarioEngine.get_scenario("Normal Office"))
    
    assert record_far.rssi < record.rssi, f"RSSI at 20m ({record_far.rssi}) should be less than RSSI at 5m ({record.rssi})"
    
    # 3. Assert Retry Rate & QoE change with SNR
    # Create extreme conditions manually for QoE and Retry tests
    # High SNR scenario
    qoe_high_snr = sim.calculate_qoe(snr=45.0, retry_rate=0.01, noise_floor=-95.0, airtime=10.0).score
    retry_high_snr = sim.calculate_retry_rate(snr=45.0)
    
    # Low SNR scenario
    qoe_low_snr = sim.calculate_qoe(snr=10.0, retry_rate=0.50, noise_floor=-85.0, airtime=80.0).score
    retry_low_snr = sim.calculate_retry_rate(snr=10.0)
    
    assert qoe_low_snr < qoe_high_snr, "QoE for low SNR should be less than high SNR"
    assert retry_high_snr < retry_low_snr, "Retry rate for high SNR should be lower than low SNR"

    # 4. Assert Microwave Noise > Normal Noise
    scenario_normal = ScenarioEngine.get_scenario("Normal Office")
    scenario_micro = ScenarioEngine.get_scenario("Microwave Burst")
    
    normal_noise = sim.calculate_noise_floor(scenario_normal)
    microwave_noise = sim.calculate_noise_floor(scenario_micro)
    
    assert microwave_noise > normal_noise, f"Microwave noise ({microwave_noise}) must be > Normal noise ({normal_noise})"

def test_scenario_recommendations():
    # Setup test AP
    ap = APState(ap_id="TEST_REC", channel=36, channel_width=40, base_noise=-95.0, x=0.0, y=0.0, tx_power_dbm=20.0, freq_mhz=5180.0)
    sim = TelemetrySimulator(ap)
    
    # 1. Normal Office -> NONE
    clients_normal = [ClientState(client_id=f"C{i}", x=3.0, y=4.0, demand_mbps=5.0, wall_count=0) for i in range(3)] # ~5m distance
    record_normal = sim.generate_telemetry(clients_normal, scenario=ScenarioEngine.get_scenario("Normal Office"))
    assert record_normal.recommendations[0]["action"] == "NONE", f"Normal Office expected NONE, got {record_normal.recommendations[0]['action']}"
    
    # 2. Microwave Burst -> CHANNEL_CHANGE
    record_micro = sim.generate_telemetry(clients_normal, scenario=ScenarioEngine.get_scenario("Microwave Burst"))
    assert record_micro.recommendations[0]["action"] == "CHANNEL_CHANGE", f"Microwave Burst expected CHANNEL_CHANGE, got {record_micro.recommendations[0]['action']}"
    
    # 3. Bluetooth Storm -> CHANNEL_CHANGE
    record_ble = sim.generate_telemetry(clients_normal, scenario=ScenarioEngine.get_scenario("Bluetooth Storm"))
    assert record_ble.recommendations[0]["action"] == "CHANNEL_CHANGE", f"Bluetooth Storm expected CHANNEL_CHANGE, got {record_ble.recommendations[0]['action']}"
    
    # 4. Neighbor AP Congestion -> LOAD_BALANCE
    record_neighbor = sim.generate_telemetry(clients_normal, scenario=ScenarioEngine.get_scenario("Neighbor AP Congestion"))
    assert record_neighbor.recommendations[0]["action"] == "LOAD_BALANCE", f"Neighbor AP Congestion expected LOAD_BALANCE, got {record_neighbor.recommendations[0]['action']}"
    
    # 5. Crowded Conference Room -> WIDTH_ADJUST
    clients_crowded = [ClientState(client_id=f"C{i}", x=4.0, y=3.0, demand_mbps=10.0, wall_count=0) for i in range(30)]
    record_crowded = sim.generate_telemetry(clients_crowded, scenario=ScenarioEngine.get_scenario("Crowded Conference Room"))
    assert record_crowded.recommendations[0]["action"] == "WIDTH_ADJUST", f"Crowded Conference Room expected WIDTH_ADJUST, got {record_crowded.recommendations[0]['action']}"
    
    # 6. Weak Signal Corner -> POWER_INCREASE
    clients_weak = [ClientState(client_id=f"C{i}", x=20.0, y=22.0, demand_mbps=5.0, wall_count=3) for i in range(2)] # ~30m distance, 3 walls
    record_weak = sim.generate_telemetry(clients_weak, scenario=ScenarioEngine.get_scenario("Weak Signal Corner"))
    assert record_weak.recommendations[0]["action"] == "POWER_INCREASE", f"Weak Signal Corner expected POWER_INCREASE, got {record_weak.recommendations[0]['action']}"

if __name__ == "__main__":
    test_formulas()
    test_scenario_recommendations()
    print("All formulas and regression checks verified successfully.")
