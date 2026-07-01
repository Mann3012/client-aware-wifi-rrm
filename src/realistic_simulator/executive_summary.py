from src.realistic_simulator.recommendation_engine import Diagnosis

def generate_executive_summary(diagnosis: Diagnosis, telemetry: dict) -> str:
    """
    Produces a dynamic executive summary based on the diagnosis and telemetry values.
    """
    retry_pct = round((telemetry.get("retry_rate", 0) or 0) * 100, 1)
    qoe_score = telemetry.get("qoe_score")
    qoe_str = f"{round(qoe_score, 1)}/100" if qoe_score is not None else "—/100"
    airtime_pct = round((telemetry.get("airtime_utilization", 0) or 0) * 100, 1)
    noise_dbm = round(telemetry.get("noise_floor", 0), 1) if telemetry.get("noise_floor") is not None else "—"

    root_cause = diagnosis.root_cause

    if "Coverage" in root_cause:
        exec_summary = f"Excessive path loss reduced RSSI and SNR. This degradation increased retransmissions ({retry_pct}%) and reduced user QoE ({qoe_str})."
    elif "Bluetooth" in root_cause:
        exec_summary = f"Intermittent Bluetooth interference increased retransmissions ({retry_pct}%) despite healthy average signal quality, reducing network efficiency and QoE ({qoe_str})."
    elif "Microwave" in root_cause:
        exec_summary = f"Broadband microwave interference increased the measured noise floor to {noise_dbm} dBm, resulting in a retry rate of {retry_pct}% and a QoE drop to {qoe_str}."
    elif "Neighbor" in root_cause or "Co-Channel" in root_cause:
        exec_summary = f"Neighbor AP traffic increased co-channel contention and reduced available capacity, elevating retries ({retry_pct}%) and lowering QoE ({qoe_str})."
    elif "Congestion" in root_cause:
        exec_summary = f"Heavy airtime utilization ({airtime_pct}%) increased contention and reduced network efficiency, leading to higher collision probabilities and lower QoE ({qoe_str})."
    elif "Healthy" in root_cause:
        exec_summary = f"Performance metrics are within healthy nominal parameters. Signal quality is adequate, retransmissions are low ({retry_pct}%), and user QoE is strong ({qoe_str})."
    else:
        exec_summary = f"Performance metrics deviated from nominal baselines. This lowered SNR, increased retransmissions ({retry_pct}%), and reduced user QoE ({qoe_str})."

    if "Healthy" not in root_cause:
        exec_summary += f" The diagnostic engine identified **{root_cause}** as the dominant root cause with {int(diagnosis.confidence*100)}% confidence and recommended **{diagnosis.recommendation}** to mitigate the issue."
    else:
        exec_summary += f" The diagnostic engine confirmed a **{root_cause}** state with {int(diagnosis.confidence*100)}% confidence."

    return exec_summary
