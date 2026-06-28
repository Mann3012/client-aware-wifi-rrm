import pytest
from src.realistic_simulator.environment import WirelessEnvironment, InterferenceSource, Point
from src.realistic_simulator.propagation import PropagationEngine
from src.realistic_simulator.constants import InterferenceType
from src.realistic_simulator.interference import InterferenceEngine

def test_frequency_overlap():
    env = WirelessEnvironment()
    prop = PropagationEngine(env)
    ie = InterferenceEngine(env, prop)
    
    # Exact match
    assert ie.calculate_frequency_overlap(5180.0, 20.0, 5180.0, 20.0) == 1.0
    
    # No overlap
    assert ie.calculate_frequency_overlap(5180.0, 20.0, 5240.0, 20.0) == 0.0
    
    # Partial overlap (10 MHz out of 20 MHz)
    assert ie.calculate_frequency_overlap(5180.0, 20.0, 5190.0, 20.0) == 0.5
    
    # TX fully swallowed by wide RX (20 MHz TX inside 80 MHz RX)
    assert ie.calculate_frequency_overlap(5210.0, 80.0, 5180.0, 20.0) == 1.0
    
    # Wide TX covering narrow RX (80 MHz TX covering 20 MHz RX)
    # The overlap fraction relative to the TX bandwidth is 20/80 = 0.25
    assert ie.calculate_frequency_overlap(5180.0, 20.0, 5210.0, 80.0) == 0.25

def test_external_interference():
    env = WirelessEnvironment()
    
    # Microwave at 2450 MHz, 50% duty cycle, 5 dBm
    mw = InterferenceSource(
        source_id="mw1", interference_type=InterferenceType.MICROWAVE,
        location=Point(10.0, 10.0), frequency_mhz=2450.0, bandwidth_mhz=20.0,
        tx_power_dbm=5.0, duty_cycle=0.5
    )
    env.interference_sources.append(mw)
    
    prop = PropagationEngine(env)
    ie = InterferenceEngine(env, prop)
    
    # Receiver exactly matching frequency
    # Overlap = 1.0, Duty Cycle = 0.5 -> Effective Fraction = 0.5 -> -3.01 dB
    # Distance = 10m. PL = FSPL(1m, 2.45GHz) + 10*3*log10(10) = ~40.2 + 30 = 70.2 dB
    # RX = 5 - 70.2 - 3.01 = -68.21 dBm
    
    powers = ie.compute_external_interference(
        rx_location=Point(0.0, 10.0),
        rx_freq_mhz=2450.0, rx_bw_mhz=20.0
    )
    
    assert len(powers) == 1
    assert powers[0] == pytest.approx(-68.2, abs=1.0)
    
    # Receiver completely off frequency
    powers_none = ie.compute_external_interference(
        rx_location=Point(0.0, 10.0),
        rx_freq_mhz=5180.0, rx_bw_mhz=20.0
    )
    assert len(powers_none) == 0
