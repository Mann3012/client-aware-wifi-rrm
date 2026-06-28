import pytest
import math
from src.realistic_simulator.channel import ChannelModel

def test_shadow_fading():
    channel = ChannelModel()
    
    # With std_dev = 0, should be exactly 0
    assert channel.shadow_fading_db(0.0) == 0.0
    
    # Over many samples, mean should be roughly 0 and std_dev roughly what we asked for
    samples = [channel.shadow_fading_db(4.0) for _ in range(10000)]
    mean = sum(samples) / len(samples)
    variance = sum((x - mean) ** 2 for x in samples) / len(samples)
    std_dev = math.sqrt(variance)
    
    assert abs(mean) < 0.2
    assert abs(std_dev - 4.0) < 0.2

def test_rayleigh_fading():
    channel = ChannelModel()
    
    # Mean of Rayleigh fading power gain in linear is 1, which means mean in dB 
    # is roughly -2.5 dB due to Jensen's inequality
    samples_db = [channel.rayleigh_fading_db() for _ in range(10000)]
    mean_db = sum(samples_db) / len(samples_db)
    
    # Expected mean of 10*log10(X) where X is Exp(1) is approx -2.506 dB
    assert -3.0 < mean_db < -2.0

def test_rician_convergence_to_rayleigh():
    channel = ChannelModel()
    
    # Very low K factor (e.g. -30 dB) should behave like Rayleigh
    rayleigh_samples = [channel.rayleigh_fading_db() for _ in range(5000)]
    rician_samples = [channel.rician_fading_db(-30.0) for _ in range(5000)]
    
    rayleigh_mean = sum(rayleigh_samples) / len(rayleigh_samples)
    rician_mean = sum(rician_samples) / len(rician_samples)
    
    # Both should be around -2.5 dB
    assert abs(rayleigh_mean - rician_mean) < 0.5

def test_doppler_and_coherence():
    channel = ChannelModel()
    
    # Walking speed 1.5 m/s at 5 GHz
    doppler = channel.doppler_shift_hz(1.5, 5e9)
    assert doppler == pytest.approx(25.0, abs=0.1) # 1.5 * 5e9 / 3e8 = 25 Hz
    
    coherence_time = channel.coherence_time_s(doppler)
    assert coherence_time == pytest.approx(0.423 / 25.0, abs=0.001)

    coherence_bw = channel.coherence_bandwidth_hz(50e-9) # 50 ns delay spread
    assert coherence_bw == pytest.approx(1 / (5 * 50e-9), abs=1) # 4 MHz
