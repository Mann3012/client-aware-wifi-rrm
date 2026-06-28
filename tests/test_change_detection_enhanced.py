import pytest
import pandas as pd
import numpy as np
from src.analytics.change_detection import (
    ChangeDetectionEngine, AlarmHysteresis, EWMADetector, CUSUMDetector
)


def test_alarm_hysteresis_activation():
    """Alarm should only fire after activation_count consecutive anomalies."""
    hyst = AlarmHysteresis(activation_count=3, cooldown_ticks=2)

    # First two consecutive anomalies → should NOT fire
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    # Third consecutive → FIRES
    assert hyst.should_fire("AP1", "retry_rate", True) is True


def test_alarm_hysteresis_cooldown():
    """After firing, alarm should be suppressed for cooldown_ticks."""
    hyst = AlarmHysteresis(activation_count=1, cooldown_ticks=3)

    # Fire immediately (activation_count=1)
    assert hyst.should_fire("AP1", "retry_rate", True) is True

    # Now in cooldown for 3 ticks — should NOT fire even if anomalous
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is False

    # Cooldown expired → can fire again
    assert hyst.should_fire("AP1", "retry_rate", True) is True


def test_alarm_hysteresis_reset_on_normal():
    """A normal reading should reset the consecutive count."""
    hyst = AlarmHysteresis(activation_count=3, cooldown_ticks=2)

    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    # Normal reading resets
    assert hyst.should_fire("AP1", "retry_rate", False) is False
    # Back to anomalous — count restarts from 0
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is True


def test_alarm_hysteresis_independent_metrics():
    """Different metrics should have independent hysteresis state."""
    hyst = AlarmHysteresis(activation_count=2, cooldown_ticks=1)

    # Retry rate fires after 2
    assert hyst.should_fire("AP1", "retry_rate", True) is False
    assert hyst.should_fire("AP1", "retry_rate", True) is True

    # Noise floor is independent — needs its own 2 consecutive
    assert hyst.should_fire("AP1", "noise_floor", True) is False
    assert hyst.should_fire("AP1", "noise_floor", True) is True


def test_change_detection_engine_with_hysteresis():
    """ChangeDetectionEngine should suppress flapping alerts via hysteresis."""
    engine = ChangeDetectionEngine()

    # Create a stable baseline of 20 data points
    timestamps = pd.date_range("2026-01-01", periods=20, freq="min")
    stable_data = {
        "timestamp": timestamps,
        "ap_id": ["AP1"] * 20,
        "retry_rate": [0.02] * 20,
        "airtime_utilization": [0.30] * 20,
        "noise_floor": [-95.0] * 20,
    }
    df = pd.DataFrame(stable_data)

    # First spike — hysteresis should suppress (need 3 consecutive)
    df_spike = df.copy()
    df_spike.loc[19, "retry_rate"] = 0.90
    alerts_1 = engine.analyze_ap_telemetry(df_spike)

    # Even if EWMA detects anomaly, hysteresis should suppress on first occurrence
    # (activation_count=3, this is only the 1st consecutive detection)
    retry_alerts = [a for a in alerts_1 if a["metric"] == "retry_rate"]
    assert len(retry_alerts) == 0
