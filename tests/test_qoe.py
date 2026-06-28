import pytest
from src.realistic_simulator.qoe import QoEEngine

def test_normalize_metric():
    qoe = QoEEngine()
    
    # Lower is better (Latency)
    assert qoe.normalize_metric(10.0, best=20.0, worst=150.0) == 1.0
    assert qoe.normalize_metric(200.0, best=20.0, worst=150.0) == 0.0
    assert qoe.normalize_metric(85.0, best=20.0, worst=150.0) == pytest.approx(0.5)
    
    # Higher is better (Throughput)
    assert qoe.normalize_metric(100.0, best=50.0, worst=0.0) == 1.0
    assert qoe.normalize_metric(0.0, best=50.0, worst=0.0) == 0.0
    assert qoe.normalize_metric(25.0, best=50.0, worst=0.0) == pytest.approx(0.5)

def test_qoe_categories():
    qoe = QoEEngine()
    assert qoe.get_category(90.0) == "Excellent"
    assert qoe.get_category(75.0) == "Good"
    assert qoe.get_category(50.0) == "Fair"
    assert qoe.get_category(20.0) == "Poor"

def test_compute_voice_qoe():
    qoe = QoEEngine()
    # Voice: sensitive to latency, jitter, loss. Not sensitive to throughput.
    
    # Perfect voice call
    res_perfect = qoe.compute_qoe(
        app_type_str="voice",
        throughput_mbps=1.0, demand_mbps=0.1,
        latency_ms=15.0, jitter_ms=2.0, packet_loss_rate=0.0001
    )
    assert res_perfect.score == 100.0
    
    # High latency voice call
    res_bad = qoe.compute_qoe(
        app_type_str="voice",
        throughput_mbps=1.0, demand_mbps=0.1,
        latency_ms=200.0, # Will zero out latency score (40% weight)
        jitter_ms=2.0, packet_loss_rate=0.0001
    )
    # Remaining score: 100% - 40% = 60%
    assert res_bad.score == pytest.approx(60.0, abs=1.0)
    assert res_bad.category == "Fair"
