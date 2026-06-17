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


class ChangeDetectionEngine:
    """
    Engine that wraps EWMA and CUSUM detectors to process raw telemetry rows and identify anomalies.
    """
    def __init__(self):
        self.ewma_detector = EWMADetector()
        self.cusum_detector = CUSUMDetector()

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
        if is_retry_anomaly:
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
        if is_airtime_anomaly:
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
        if is_noise_anomaly:
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
