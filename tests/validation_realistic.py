import os
import sys
import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analytics.change_detection import ChangeDetectionEngine

def run_validation():
    engine = ChangeDetectionEngine()
    print("Running Realistic Simulator Validation against EWMA & CUSUM...")
    print("-" * 60)

    # Base dataset generator
    def generate_base_df(length=20):
        timestamps = [(datetime.datetime.now() - datetime.timedelta(minutes=length-i)).isoformat() for i in range(length)]
        return pd.DataFrame({
            "timestamp": timestamps,
            "ap_id": ["AP_001"] * length,
            "retry_rate": [0.05] * length,
            "airtime_utilization": [0.20] * length,
            "noise_floor": [-95.0] * length
        })

    # ==========================================
    # SCENARIO A: CUSUM Microwave Detection
    # ==========================================
    print("\nScenario A: Microwave Interference (Noise Floor Jump -95 -> -80)")
    df_a = generate_base_df()
    
    # Inject Microwave Event for the last 3 data points
    df_a.loc[df_a.index[-3:], "noise_floor"] = -80.0
    
    alerts_a = engine.analyze_ap_telemetry(df_a)
    has_cusum_alert = any(a["alert_type"] == "abnormal_interference" for a in alerts_a)
    
    if has_cusum_alert:
        print("[PASS] CUSUM successfully detected the noise floor shift.")
    else:
        print("[FAIL] CUSUM missed the noise floor shift!")
        
    for alert in alerts_a:
        print(f"  -> Generated: {alert['alert_type']} ({alert['description']})")

    # ==========================================
    # SCENARIO B: EWMA Retry Rate Spike
    # ==========================================
    print("\nScenario B: Congestion Spike (Retry Rate 5% -> 35%)")
    df_b = generate_base_df()
    
    # Gradual/sudden spike in retry rate due to congestion
    df_b.loc[df_b.index[-2:], "retry_rate"] = [0.15, 0.35]
    
    alerts_b = engine.analyze_ap_telemetry(df_b)
    has_ewma_alert = any(a["alert_type"] == "retry_spike" for a in alerts_b)
    
    if has_ewma_alert:
        print("[PASS] EWMA successfully detected the retry rate spike.")
    else:
        print("[FAIL] EWMA missed the retry rate spike!")
        
    for alert in alerts_b:
        print(f"  -> Generated: {alert['alert_type']} ({alert['description']})")

    # Final assertion
    assert has_cusum_alert, "CUSUM Validation Failed"
    assert has_ewma_alert, "EWMA Validation Failed"
    print("\n" + "=" * 60)
    print("ALL VALIDATION TESTS PASSED.")

if __name__ == "__main__":
    run_validation()
