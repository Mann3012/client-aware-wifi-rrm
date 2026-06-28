import pytest
from src.realistic_simulator.wifi6_phy import WiFi6Phy, WiFi6PhyConfig
from src.realistic_simulator.link_adaptation import LinkAdaptation
from src.realistic_simulator.constants import MCS_TABLE

def test_wifi6_phy_hierarchy_allocations():
    # 20 MHz
    alloc_20 = WiFi6PhyConfig.get_subcarrier_allocation(20)
    assert alloc_20.fft_size == 256
    assert alloc_20.data_subcarriers == 234
    
    # 80 MHz
    alloc_80 = WiFi6PhyConfig.get_subcarrier_allocation(80)
    assert alloc_80.fft_size == 1024
    assert alloc_80.data_subcarriers == 980
    
def test_ofdm_symbol_duration():
    assert WiFi6PhyConfig.ofdm_symbol_duration_us(0.8) == pytest.approx(13.6)
    assert WiFi6PhyConfig.ofdm_symbol_duration_us(1.6) == pytest.approx(14.4)
    assert WiFi6PhyConfig.ofdm_symbol_duration_us(3.2) == pytest.approx(16.0)

def test_link_adaptation():
    la = LinkAdaptation(max_spatial_streams=2)
    
    # 35 dB SINR -> MCS 11
    mcs_excellent = la.select_mcs(35.0)
    assert mcs_excellent.index == 11
    
    # 35 dB SINR but 50% retries -> effective SINR 30 dB -> MCS 10
    mcs_retry = la.select_mcs(35.0, retry_rate=0.5)
    assert mcs_retry.index == 10
    
    # 0 dB SINR -> MCS 0
    mcs_poor = la.select_mcs(0.0)
    assert mcs_poor.index == 0

def test_phy_rate_computation():
    la = LinkAdaptation(max_spatial_streams=2)
    
    # Test known rate: MCS 11, 80 MHz, 2SS, 0.8 us GI
    # Nsd = 980
    # Nbpscs = 8.3333333333 (1024-QAM 5/6 = 10 * 5/6 = 8.3333)
    # Nss = 2
    # T_sym = 13.6 us
    # Rate = (980 * 8.3333 * 2) / 13.6 = 1200.98 Mbps ≈ 1201 Mbps
    
    phy = WiFi6Phy(bandwidth_mhz=80, spatial_streams=2, guard_interval_us=0.8)
    mcs = MCS_TABLE[11]  # MCS 11
    
    rate = phy.compute_phy_rate_mbps(mcs)
    
    assert rate == pytest.approx(1200.98, abs=0.1)
    
    # Same thing but 40 MHz (Nsd=468). Rate ≈ 573.5 Mbps
    phy_40 = WiFi6Phy(bandwidth_mhz=40, spatial_streams=2, guard_interval_us=0.8)
    rate_40 = phy_40.compute_phy_rate_mbps(mcs)
    assert rate_40 == pytest.approx(573.5, abs=0.1)

def test_per_monotonicity():
    phy = WiFi6Phy(bandwidth_mhz=80, spatial_streams=2, guard_interval_us=0.8)
    mcs = MCS_TABLE[5] # MCS 5, min SINR = 15 dB
    
    # Very good SINR -> PER ≈ 0
    per_good = phy.compute_per(sinr_db=20.0, mcs=mcs)
    assert per_good == 0.001
    
    # Exactly at threshold -> PER ≈ 0.5
    per_thresh = phy.compute_per(sinr_db=15.0, mcs=mcs)
    assert per_thresh == pytest.approx(0.5, abs=0.01)
    
    # Very bad SINR -> PER ≈ 1
    per_bad = phy.compute_per(sinr_db=10.0, mcs=mcs)
    assert per_bad == 0.999
