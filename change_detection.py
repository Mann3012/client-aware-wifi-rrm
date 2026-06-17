import pandas as pd
import numpy as np
import datetime
from typing import List, Dict, Any, Tuple

class EWMADetector:
    """
    Exponentially Weighted Moving Average (EWMA) Detector.
    Tracks moving average and deviations to detect sudden spike anomalies.
    """
    def __init__(self, span: int = 10, threshold_stdevs: float = 3.0):
        self.span = span
        self.threshold_stdevs = threshold_stdevs

    def detect(self, series: pd.Series) -> Tuple[bool, float, float, str]:
        """
        Analyzes a series and checks if the last data point is anomalous.
        Returns (is_anomaly, current_value, threshold_value, description)
        """
        if len(series) < self.span:
            return False, 0.0, 0.0, "Insufficient data points for EWMA baseline."

        # Calculate EWMA on the series
        ewma_mean = series.ewm(span=self.span, adjust=False).mean()
        
        # Calculate overall standard deviation as historical baseline
        std_dev = series.std()
        if pd.isna(std_dev) or std_dev == 0:
            std_dev = 1e-5

        last_val = float(series.iloc[-1])
        # Get the previous step's EWMA mean to check the current value against it
        last_mean = float(ewma_mean.iloc[-2]) if len(ewma_mean) > 1 else float(ewma_mean.iloc[-1])
        
        z_score = (last_val - last_mean) / std_dev
        threshold_val = last_mean + (self.threshold_stdevs * std_dev)
        is_anomaly = z_score > self.threshold_stdevs

        description = (
            f"EWMA spike anomaly: Value {last_val:.4f} is {z_score:.2f} standard deviations "
            f"above the moving average of {last_mean:.4f} (Threshold: {threshold_val:.4f})"
        )

        return is_anomaly, last_val, threshold_val, description


class CUSUMDetector:
    """
    Cumulative Sum (CUSUM) Detector.
    Tracks cumulative sums of deviations to detect small, persistent shifts in means.
    """
    def __init__(self, threshold: float = 5.0, drift: float = 0.5):
        self.threshold = threshold  # Decision interval (H)
        self.drift = drift          # Allowance/slack parameter (K)

    def detect(self, series: pd.Series) -> Tuple[bool, float, float, str]:
        """
        Analyzes a series and checks if the cumulative sum of deviations signals a shift.
        Returns (is_anomaly, current_value, threshold_value, description)
        """
        if len(series) < 10:
            return False, 0.0, 0.0, "Insufficient data points for CUSUM baseline."

        # Calculate baseline metrics excluding the latest point
        baseline = series.iloc[:-1]
        mean = baseline.mean()
        std = baseline.std()
        if pd.isna(std) or std == 0:
            std = 1e-5

        # Standardize the entire series relative to the baseline
        standardized = (series - mean) / std

        # High-side CUSUM loop
        s_high = np.zeros(len(standardized))
        for i in range(1, len(standardized)):
            s_high[i] = max(0.0, s_high[i-1] + standardized.iloc[i] - self.drift)

        last_cusum = float(s_high[-1])
        last_val = float(series.iloc[-1])
        is_anomaly = last_cusum > self.threshold
        
        # Absolute metric value threshold equivalent
        threshold_metric_val = mean + (self.threshold * std)

        description = (
            f"CUSUM mean-shift anomaly: Cumulative sum {last_cusum:.2f} "
            f"exceeded threshold {self.threshold:.2f} (Baseline mean: {mean:.2f}, std: {std:.2f})"
        )

        return is_anomaly, last_val, threshold_metric_val, description


class ChangeDetectionEngine:
    """
    Engine that analyzes a DataFrame of telemetry data and returns Alert objects.
    """
    def __init__(self):
        self.ewma = EWMADetector()
        self.cusum = CUSUMDetector()

    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Processes a dataframe of telemetry. Expects sorted chronological data for a single AP.
        Returns a list of alert dictionaries.
        """
        if df.empty or len(df) < 10:
            return []

        alerts = []
        ap_id = df['ap_id'].iloc[0]
        latest_timestamp = df['timestamp'].iloc[-1]

        # 1. Detect Retry Rate spikes (EWMA)
        is_retry, val, thresh, desc = self.ewma.detect(df['retry_rate'])
        if is_retry:
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "retry_spike",
                "metric": "retry_rate",
                "value": round(val, 4),
                "threshold": round(thresh, 4),
                "description": desc
            })

        # 2. Detect Airtime Congestion (EWMA)
        is_airtime, val, thresh, desc = self.ewma.detect(df['airtime_utilization'])
        if is_airtime:
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "airtime_congestion",
                "metric": "airtime_utilization",
                "value": round(val, 4),
                "threshold": round(thresh, 4),
                "description": desc
            })

        # 3. Detect Noise Floor shifts / Interference (CUSUM)
        is_noise, val, thresh, desc = self.cusum.detect(df['noise_floor'])
        if is_noise:
            alerts.append({
                "timestamp": latest_timestamp,
                "ap_id": ap_id,
                "alert_type": "abnormal_interference",
                "metric": "noise_floor",
                "value": round(val, 2),
                "threshold": round(thresh, 2),
                "description": desc
            })

        return alerts


# ==========================================
# Example Usage Execution Block
# ==========================================
if __name__ == "__main__":
    print("Change Detection Engine Example Run")
    print("====================================")
    
    # 1. Create a simulated chronological dataset for a single AP (30 steps)
    timestamps = [
        (datetime.datetime.now() - datetime.timedelta(minutes=30-i)).isoformat()
        for i in range(30)
    ]
    
    # Base telemetry structure
    data = {
        "timestamp": timestamps,
        "ap_id": ["AP_001"] * 30,
        "retry_rate": [0.02] * 29 + [0.35],            # Intentionally inject a retry spike at step 30
        "airtime_utilization": [0.20] * 30,             # Keep airtime stable
        "noise_floor": [-96.0] * 20 + [-80.0] * 10       # Intentionally shift the mean noise floor at step 20+
    }
    
    df = pd.DataFrame(data)
    print("Simulated dataset head:")
    print(df.tail(5))
    print()

    # 2. Run analysis on the cumulative window
    engine = ChangeDetectionEngine()
    
    # Analyze prefix slices to simulate a stream and show detection behavior
    print("Simulating streaming data analysis:")
    
    # Check at step 20 (just before noise shift is fully established)
    print("\n--- Analyzing at Step 20 (Normal state) ---")
    alerts_step20 = engine.analyze(df.iloc[:20])
    print(f"Alerts generated: {len(alerts_step20)}")
    
    # Check at step 25 (after noise floor has shifted persistently for 5 minutes)
    print("\n--- Analyzing at Step 25 (Noise shift in progress) ---")
    alerts_step25 = engine.analyze(df.iloc[:25])
    for alert in alerts_step25:
        print(f"[{alert['alert_type'].upper()}] on AP: {alert['ap_id']} - {alert['description']}")

    # Check at step 30 (after sudden retry spike)
    print("\n--- Analyzing at Step 30 (Retry rate spike & active noise shift) ---")
    alerts_step30 = engine.analyze(df)
    for alert in alerts_step30:
        print(f"[{alert['alert_type'].upper()}] on AP: {alert['ap_id']} - {alert['description']}")
