import pytest
from src.realistic_simulator.traffic_model import TrafficModel
from src.realistic_simulator.wifi6_phy import PhyResult
from src.realistic_simulator.mac_layer import MacResult

def test_mathis_tcp_throughput():
    tm = TrafficModel(mss_bytes=1460)
    
    # No loss -> bounded by link capacity
    tpt_noloss = tm.compute_mathis_tcp_throughput(base_rtt_ms=10.0, packet_loss_rate=0.0, link_capacity_mbps=100.0)
    assert tpt_noloss == 100.0
    
    # 1% loss at 10ms RTT
    # MSS_bits = 11680. Rate = (11680 / 0.01) * (1.22 / sqrt(0.01))
    # = 1,168,000 * 12.2 = 14,249,600 bps = 14.24 Mbps
    tpt_loss = tm.compute_mathis_tcp_throughput(base_rtt_ms=10.0, packet_loss_rate=0.01, link_capacity_mbps=100.0)
    assert tpt_loss == pytest.approx(14.25, abs=0.1)

def test_queuing_delay():
    tm = TrafficModel()
    
    # Demand = 50 Mbps, Capacity = 100 Mbps (50% utilization)
    # Arrival rate = 50,000,000 / 12000 = 4166.6 pkts/s
    # Service rate = 100,000,000 / 12000 = 8333.3 pkts/s
    # Delay = 1 / (8333.3 - 4166.6) = 1 / 4166.6 = 0.00024 seconds = 0.24 ms
    delay = tm.compute_queuing_delay(demand_mbps=50.0, capacity_mbps=100.0)
    assert delay == pytest.approx(0.24, abs=0.05)
    
    # Very high utilization (> 99%)
    delay_high = tm.compute_queuing_delay(demand_mbps=99.5, capacity_mbps=100.0)
    assert delay_high == 500.0 # capped

def test_evaluate_traffic():
    tm = TrafficModel()
    phy = PhyResult(mcs_index=5, phy_rate_mbps=300.0, per=0.02, spatial_streams=2, guard_interval_us=0.8)
    mac = MacResult(total_frame_time_us=300.0, payload_time_us=100.0, overhead_time_us=200.0, mac_efficiency=0.5, effective_throughput_mbps=150.0)
    
    res = tm.evaluate_traffic(demand_mbps=20.0, phy_result=phy, mac_result=mac)
    
    # TCP Throughput with 2% loss and 10ms RTT is around 10 Mbps.
    # So demand of 20 Mbps is not satisfied
    assert res.l4_throughput_mbps < 20.0
    assert not res.demand_satisfied
    
    # UDP ignores Mathis TCP math
    res_udp = tm.evaluate_traffic(demand_mbps=20.0, phy_result=phy, mac_result=mac, is_udp=True)
    assert res_udp.l4_throughput_mbps == pytest.approx(20.0, abs=0.1) # 20 * (1 - 0.02)
    assert res_udp.demand_satisfied
