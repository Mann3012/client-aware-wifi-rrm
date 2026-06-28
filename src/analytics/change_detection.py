import os
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load config thresholds
load_dotenv()
EWMA_SPAN = int(os.getenv("EWMA_SPAN", 10))
EWMA_THRESHOLD_STDEVS = float(os.getenv("EWMA_THRESHOLD_STDEVS", 3.0))
CUSUM_THRESHOLD = float(os.getenv("CUSUM_THRESHOLD", 5.0))
CUSUM_DRIFT = float(os.getenv("CUSUM_DRIFT", 0.5))

logger = logging.getLogger("RRM.Analytics")

class EWMADetector:
    """
    Exponentially Weighted Moving Average (EWMA) Detector.
    Used for smoothing high-frequency noise and identifying short-term deviations.
    """
    def __init__(self, span: int = EWMA_SPAN, threshold_stdevs: float = EWMA_THRESHOLD_STDEVS):
        self.span = span
        self.alpha = 2.0 / (span + 1.0)
        self.threshold_stdevs = threshold_stdevs

    def detect(self, series: pd.Series) -> Tuple[bool, float, float, str]:
        """
        Analyzes a time series of a metric and checks if the last point is anomalous.
        Returns:
            is_anomaly (bool)
            current_value (float)
            threshold_value (float)
            description (str)
        """
        if len(series) < self.span:
            return False, 0.0, 0.0, "Insufficient data for EWMA calculation"

        # Calculate EWMA mean and standard deviation
        ewma_mean = series.ewm(span=self.span, adjust=False).mean()
        # Compute standard deviation on a rolling window or overall to establish standard baseline
        std_dev = series.std()
        if pd.isna(std_dev) or std_dev == 0:
            std_dev = 1e-5 # Avoid division by zero/NaN

        last_val = float(series.iloc[-1])
        last_mean = float(ewma_mean.iloc[-2]) if len(ewma_mean) > 1 else float(ewma_mean.iloc[-1])
        z_score = (last_val - last_mean) / std_dev
        threshold_val = last_mean + (self.threshold_stdevs * std_dev)

        is_anomaly = z_score > self.threshold_stdevs
        
        description = (
            f"EWMA deviation detected: Value {last_val:.4f} is {z_score:.2f} standard deviations "
            f"above the moving average of {last_mean:.4f} (Threshold: {threshold_val:.4f})"
        )
        
        return is_anomaly, last_val, threshold_val, description


class CUSUMDetector:
    """
    Cumulative Sum (CUSUM) Detector.
    Used to detect small, persistent shifts in the mean of a metric.
    Specifically targets increases in metrics (e.g. noise floor, retry rate).
    """
    def __init__(self, threshold: float = CUSUM_THRESHOLD, drift: float = CUSUM_DRIFT):
        self.threshold = threshold  # Decision interval (H)
        self.drift = drift          # Allowance/slack parameter (K)

    def detect(self, series: pd.Series) -> Tuple[bool, float, float, str]:
        """
        Calculates CUSUM on the series and returns whether a change occurred at the latest point.
        Returns:
            is_anomaly (bool)
            current_value (float)
            threshold_value (float)
            description (str)
        """
        if len(series) < 10:
            return False, 0.0, 0.0, "Insufficient data for CUSUM calculation"

        # Standardize the data relative to baseline (excluding the current point to get baseline)
        baseline = series.iloc[:-1]
        mean = baseline.mean()
        std = baseline.std()
        if pd.isna(std) or std == 0:
            std = 1e-5

        # Compute standard values for the entire series
        standardized = (series - mean) / std

        # Run high-side CUSUM algorithm
        s_high = np.zeros(len(standardized))
        for i in range(1, len(standardized)):
            # S_H(i) = max(0, S_H(i-1) + z(i) - K)
            s_high[i] = max(0.0, s_high[i-1] + standardized.iloc[i] - self.drift)

        last_cusum = float(s_high[-1])
        last_val = float(series.iloc[-1])
        
        is_anomaly = last_cusum > self.threshold
        
        # Threshold in metric space corresponding to standard deviation scale
        threshold_metric_val = mean + (self.threshold * std)
        
        description = (
            f"CUSUM shift detected: Cumulative deviation {last_cusum:.2f} "
            f"exceeded threshold {self.threshold:.2f} (Baseline mean: {mean:.2f}, std: {std:.2f})"
        )

        return is_anomaly, last_val, threshold_metric_val, description


# ─────────────────────────────────────────────────────────────────────────────
# Alarm Hysteresis (Iteration 4 Enhancement)
# ─────────────────────────────────────────────────────────────────────────────

class AlarmHysteresis:
    """Prevents alert flapping by requiring an alarm condition to persist
    for a minimum number of consecutive ticks before firing, and then
    enforcing a cooldown period before the same alarm can fire again.

    This models the hysteresis behavior described in the Arista RRM architecture
    where rapid oscillation of RRM actions must be prevented.
    """
    def __init__(self, activation_count: int = 3, cooldown_ticks: int = 5):
        """
        Args:
            activation_count: Number of consecutive anomalous readings required
                              before the alarm fires.
            cooldown_ticks: Number of ticks after an alarm fires before it can
                            fire again (even if conditions persist).
        """
        self.activation_count = activation_count
        self.cooldown_ticks = cooldown_ticks

        # State per (ap_id, metric) pair
        self._consecutive_counts: Dict[str, int] = {}
        self._cooldown_remaining: Dict[str, int] = {}

    def _key(self, ap_id: str, metric: str) -> str:
        return f"{ap_id}::{metric}"

    def should_fire(self, ap_id: str, metric: str, is_anomaly: bool) -> bool:
        """Evaluates whether an alert should actually fire given hysteresis state.

        Args:
            ap_id: The access point identifier.
            metric: The metric name (e.g., "retry_rate", "noise_floor").
            is_anomaly: Whether the raw detector flagged this tick as anomalous.

        Returns:
            True if the alert should fire (consecutive threshold met and not in cooldown).
        """
        key = self._key(ap_id, metric)

        # Tick down cooldowns
        if key in self._cooldown_remaining:
            if self._cooldown_remaining[key] > 0:
                self._cooldown_remaining[key] -= 1
                # During cooldown, reset consecutive count and suppress
                self._consecutive_counts[key] = 0
                return False

        if is_anomaly:
            self._consecutive_counts[key] = self._consecutive_counts.get(key, 0) + 1
        else:
            self._consecutive_counts[key] = 0
            return False

        if self._consecutive_counts[key] >= self.activation_count:
            # Fire the alarm and start cooldown
            self._consecutive_counts[key] = 0
            self._cooldown_remaining[key] = self.cooldown_ticks
            logger.info(
                "Alarm fired for %s/%s after %d consecutive detections. "
                "Cooldown: %d ticks.",
                ap_id, metric, self.activation_count, self.cooldown_ticks,
            )
            return True

        return False

    def reset(self, ap_id: str, metric: str) -> None:
        """Manually resets hysteresis state for a specific alarm."""
        key = self._key(ap_id, metric)
        self._consecutive_counts.pop(key, None)
        self._cooldown_remaining.pop(key, None)


class ChangeDetectionEngine:
    """
    Engine that wraps EWMA and CUSUM detectors to process raw telemetry rows and identify anomalies.
    Enhanced in Iteration 4 with alarm hysteresis to prevent flapping.
    """
    def __init__(self):
        self.ewma_detector = EWMADetector()
        self.cusum_detector = CUSUMDetector()
        self.hysteresis = AlarmHysteresis(activation_count=3, cooldown_ticks=5)

    def analyze_ap_telemetry(self, df_telemetry: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Processes historical telemetry data for a SINGLE Access Point.
        Assumes data is sorted chronologically.
        Returns a list of dicts representing detected alerts to be inserted into the database.
        """
        if df_telemetry.empty or len(df_telemetry) < 10:
            return []

        alerts = []
        ap_id = df_telemetry['ap_id'].iloc[0]
        latest_timestamp = df_telemetry['timestamp'].iloc[-1]

        # 1. Check for Retry Rate Spike (using EWMA)
        retry_series = df_telemetry['retry_rate']
        is_retry_anomaly, val, thresh, desc = self.ewma_detector.detect(retry_series)
        if self.hysteresis.should_fire(ap_id, "retry_rate", is_retry_anomaly):
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "retry_spike",
                "metric": "retry_rate",
                "value": val,
                "threshold": thresh,
                "description": f"EWMA: {desc}"
            })

        # 2. Check for Airtime Congestion (using EWMA)
        airtime_series = df_telemetry['airtime_utilization']
        is_airtime_anomaly, val, thresh, desc = self.ewma_detector.detect(airtime_series)
        if self.hysteresis.should_fire(ap_id, "airtime_utilization", is_airtime_anomaly):
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "airtime_congestion",
                "metric": "airtime_utilization",
                "value": val,
                "threshold": thresh,
                "description": f"EWMA: {desc}"
            })

        # 3. Check for Persistent Interference / Noise Floor Shift (using CUSUM)
        noise_series = df_telemetry['noise_floor']
        is_noise_anomaly, val, thresh, desc = self.cusum_detector.detect(noise_series)
        if self.hysteresis.should_fire(ap_id, "noise_floor", is_noise_anomaly):
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "abnormal_interference",
                "metric": "noise_floor",
                "value": val,
                "threshold": thresh,
                "description": f"CUSUM: {desc}"
            })

        return alerts
