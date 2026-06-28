import pytest
from src.realistic_simulator.receiver import ReceiverModel

def test_thermal_noise_floor():
    rx = ReceiverModel(noise_figure_db=5.0)
    
    # Noise floor for 20 MHz (20e6 Hz) = -174 + 10*log10(20e6) + 5 = -95.99 dBm
    noise_20mhz = rx.thermal_noise_floor_dbm(20e6)
    assert noise_20mhz == pytest.approx(-95.99, abs=0.05)
    
    # Doubling bandwidth should add exactly 10*log10(2) ≈ 3.01 dB
    noise_40mhz = rx.thermal_noise_floor_dbm(40e6)
    assert noise_40mhz - noise_20mhz == pytest.approx(3.01, abs=0.01)

def test_compute_rssi():
    rx = ReceiverModel(noise_figure_db=5.0)
    
    # RSSI = TxPower(20) + TxGain(3) + RxGain(0) - ChannelLoss(85) = -62 dBm
    rssi = rx.compute_rssi(tx_power_dbm=20.0, tx_antenna_gain_dbi=3.0, 
                           rx_antenna_gain_dbi=0.0, total_channel_loss_db=85.0)
    assert rssi == -62.0

def test_compute_snr():
    rx = ReceiverModel(noise_figure_db=5.0)
    snr = rx.compute_snr(rssi_dbm=-60.0, noise_floor_dbm=-95.0)
    assert snr == 35.0

def test_compute_sinr():
    rx = ReceiverModel(noise_figure_db=5.0)
    
    # Signal -60 dBm, Noise -95 dBm. 
    # Interference 1: -60 dBm
    # Since interference == signal, SINR should be ~0 dB
    sinr = rx.compute_sinr(-60.0, -95.0, [-60.0])
    assert sinr == pytest.approx(0.0, abs=0.1)
    
    # Two interferers at -60 dBm -> combined interference is -57 dBm. 
    # Signal is 3 dB weaker than interference, so SINR ~-3 dB
    sinr_2 = rx.compute_sinr(-60.0, -95.0, [-60.0, -60.0])
    assert sinr_2 == pytest.approx(-3.0, abs=0.1)
