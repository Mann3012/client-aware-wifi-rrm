import pytest
from src.realistic_simulator.additional_radio import SensingRadio, SpectrumSnapshot
from src.realistic_simulator.environment import (
    WirelessEnvironment, Point, InterferenceSource, create_office_environment,
)
from src.realistic_simulator.constants import InterferenceType


def test_fft_sweep_clean_channel():
    """A clean channel (no interference) should have all bins near the noise floor."""
    env = create_office_environment()
    radio = SensingRadio(noise_figure_db=5.0)
    ap_loc = Point(20.0, 15.0)

    snapshot = radio.perform_fft_sweep(
        channel=36, bandwidth_mhz=20, environment=env, ap_location=ap_loc
    )

    assert snapshot.channel == 36
    assert snapshot.bandwidth_mhz == 20
    assert len(snapshot.bins) == 256  # FFT size for 20 MHz
    # No interference → busy fraction should be very low
    assert snapshot.channel_busy_fraction < 0.05
    # Peak should be close to noise floor
    assert snapshot.peak_power_dbm < snapshot.noise_floor_dbm + 10.0


def test_fft_sweep_with_interference():
    """An interferer on-channel should raise power in affected bins."""
    env = create_office_environment()
    # Add a strong microwave interferer close to the AP
    env.interference_sources.append(InterferenceSource(
        source_id="mw1",
        interference_type=InterferenceType.MICROWAVE,
        location=Point(22.0, 15.0),  # 2m away
        frequency_mhz=5180.0,
        bandwidth_mhz=20.0,
        tx_power_dbm=15.0,
        duty_cycle=1.0,  # Always on for deterministic test
    ))

    radio = SensingRadio(noise_figure_db=5.0)
    snapshot = radio.perform_fft_sweep(
        channel=36, bandwidth_mhz=20, environment=env, ap_location=Point(20.0, 15.0)
    )

    # With a strong on-channel interferer, busy fraction should be significant
    assert snapshot.channel_busy_fraction > 0.2
    # Peak power should be well above noise floor
    assert snapshot.peak_power_dbm > snapshot.noise_floor_dbm + 6.0


def test_classify_interferers_wifi():
    """A broadband (≥20 MHz) detected energy region should classify as WiFi."""
    env = create_office_environment()
    env.interference_sources.append(InterferenceSource(
        source_id="neighbor_ap",
        interference_type=InterferenceType.NEIGHBOR_AP,
        location=Point(22.0, 15.0),
        frequency_mhz=5180.0,
        bandwidth_mhz=20.0,
        tx_power_dbm=15.0,
        duty_cycle=1.0,
    ))

    radio = SensingRadio(noise_figure_db=5.0)
    snapshot = radio.perform_fft_sweep(
        channel=36, bandwidth_mhz=20, environment=env, ap_location=Point(20.0, 15.0)
    )
    interferers = radio.classify_interferers(snapshot)

    # Should detect at least one interferer
    assert len(interferers) >= 1
    # The broadband one should be classified as wifi
    wifi_intfs = [i for i in interferers if i.classification == "wifi"]
    assert len(wifi_intfs) >= 1


def test_channel_quality_score():
    """Channel quality should be high for clean channels and low for noisy ones."""
    radio = SensingRadio(noise_figure_db=5.0)

    # Clean channel
    env_clean = create_office_environment()
    report_clean = radio.scan(
        channel=36, bandwidth_mhz=20, environment=env_clean, ap_location=Point(20.0, 15.0)
    )
    assert report_clean.channel_quality_score > 80.0

    # Noisy channel
    env_noisy = create_office_environment()
    env_noisy.interference_sources.append(InterferenceSource(
        source_id="mw1",
        interference_type=InterferenceType.MICROWAVE,
        location=Point(21.0, 15.0),
        frequency_mhz=5180.0,
        bandwidth_mhz=20.0,
        tx_power_dbm=20.0,
        duty_cycle=1.0,
    ))
    report_noisy = radio.scan(
        channel=36, bandwidth_mhz=20, environment=env_noisy, ap_location=Point(20.0, 15.0)
    )
    assert report_noisy.channel_quality_score < report_clean.channel_quality_score


def test_sensing_report_serialization():
    """SensingRadioReport.to_dict() should produce a valid dictionary."""
    radio = SensingRadio()
    env = create_office_environment()
    report = radio.scan(
        channel=36, bandwidth_mhz=20, environment=env, ap_location=Point(20.0, 15.0)
    )
    d = report.to_dict()
    assert "spectrum" in d
    assert "detected_interferers" in d
    assert "channel_quality_score" in d
    assert d["spectrum"]["num_bins"] == 256
