import pytest
from src.realistic_simulator.mac_layer import MacLayer
from src.realistic_simulator.wifi6_phy import PhyResult

def test_average_backoff():
    mac = MacLayer()
    # At p=0, backoff should be CW_MIN/2 slots = 7.5 slots
    # 7.5 * 9 us = 67.5 us
    assert mac.average_backoff_us(0.0) == 67.5
    
    # At p=1, it hits CW_MAX
    # CW_MAX / 2 = 1023 / 2 = 511.5 slots -> 511.5 * 9 = 4603.5 us
    assert mac.average_backoff_us(1.0) == 4603.5

def test_rts_cts_overhead():
    mac = MacLayer()
    # RTS payload: 20 bytes * 8 / 6 Mbps = 26.66 us
    # CTS payload: 14 bytes * 8 / 6 Mbps = 18.66 us
    # Overheads: 100(pre) + 20(hdr) = 120 per frame
    # SIFS = 16 us * 2
    # Total = (120 + 26.66) + 16 + (120 + 18.66) + 16 = 317.33 us
    overhead = mac.compute_rts_cts_overhead_us(6.0)
    assert overhead == pytest.approx(317.33, abs=0.1)

def test_transmission_time():
    mac = MacLayer(rts_cts_threshold_bytes=2347)
    
    # Perfect PHY, 1500 byte payload
    # 1500 bytes = 12000 bits. At 1200 Mbps, payload time = 10 us
    # Overhead: DIFS(34) + Backoff(67.5) + Preamble(100) + PHYHdr(20) + SIFS(16) + ACK(44) = 281.5 us
    # Total frame time = 281.5 + 10 = 291.5 us
    phy = PhyResult(mcs_index=11, phy_rate_mbps=1200.0, per=0.0, spatial_streams=2, guard_interval_us=0.8)
    
    result = mac.compute_transmission_time(packet_length_bytes=1500, phy_result=phy)
    
    assert result.payload_time_us == pytest.approx(10.24, abs=0.1) # 1536 * 8 / 1200 = 10.24 (includes MAC header)
    assert result.overhead_time_us == pytest.approx(281.5, abs=0.1)
    
    # Efficiency is useful payload time / total time
    # Useful = 1500 * 8 / 1200 = 10 us
    # Total = 281.5 + 10.24 = 291.74 us
    # Eff = 10 / 291.74 = 3.4%
    assert result.mac_efficiency == pytest.approx(0.034, abs=0.005)
    
    # If we aggregate 64 frames (A-MPDU), efficiency shoots up
    result_ampdu = mac.compute_transmission_time(packet_length_bytes=1500, phy_result=phy, aggregated_frames=64)
    # Useful payload = 640 us. Overhead remains similar (RTS/CTS kicks in though)
    assert result_ampdu.mac_efficiency > 0.50 # Greater than 50%
