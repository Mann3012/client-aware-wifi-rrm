import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON
from src.database.connection import Base
from src.database.connection import Base

class Telemetry(Base):
    """
    Model representing raw WiFi Access Point telemetry data.
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    ap_id = Column(String(50), index=True, nullable=False)
    channel = Column(Integer, nullable=False)
    rssi = Column(Float, nullable=False)             # Client RSSI average (dBm)
    snr = Column(Float, nullable=False)              # Client SNR average (dB)
    noise_floor = Column(Float, nullable=False)      # Noise floor (dBm)
    airtime_utilization = Column(Float, nullable=False) # Airtime occupancy (0.0 to 1.0)
    retry_rate = Column(Float, nullable=False)       # Packet retry rate (0.0 to 1.0)
    client_count = Column(Integer, nullable=False)   # Number of active clients
    
    # Realistic Simulator Fields
    qoe_score = Column(Float, nullable=True)         # Calculated QoE 0-100
    qoe_category = Column(String(50), nullable=True) # Excellent, Good, Fair, Poor
    interference_type = Column(String(50), nullable=True) # None, Microwave, BLE, NeighborAP
    distance = Column(Float, nullable=True)          # Euclidean distance
    max_distance = Column(Float, nullable=True)      # Max client distance
    closest_client = Column(Float, nullable=True)    # Min client distance
    furthest_client = Column(Float, nullable=True)   # Same as max distance conceptually but stored explicit
    freq_mhz = Column(Float, nullable=True)          # AP operating frequency in MHz
    tx_power = Column(Float, nullable=True)          # AP transmit power in dBm
    wall_count = Column(Integer, nullable=True)      # Number of walls between AP and client
    wall_loss = Column(Float, nullable=True)         # Obstacle attenuation in dB
    scenario_name = Column(String(100), default="Normal Office") # Active scenario name
    
    # Representative-client per-link fields (Nullable for backward compatibility)
    path_loss_db           = Column(Float, nullable=True)  # Representative client path loss (dB)
    estimated_rx_power_dbm = Column(Float, nullable=True)  # Deterministic link-budget RX power (dBm)
    sinr_db                = Column(Float, nullable=True)  # Representative client SINR (dB)
    mcs_index              = Column(Float, nullable=True)  # Representative client MCS index
    phy_rate_mbps          = Column(Float, nullable=True)  # Representative client PHY rate (Mbps)
    latency_ms             = Column(Float, nullable=True)  # Representative client end-to-end latency (ms)
    throughput_mbps        = Column(Float, nullable=True)  # Representative client L4 throughput (Mbps)

    # Iteration 4 Extension: Sensing Radio Snapshot
    spectrum_snapshot = Column(JSON, nullable=True)  # JSON serialization of sensing radio report

    def __repr__(self):
        return f"<Telemetry ap_id={self.ap_id} timestamp={self.timestamp} channel={self.channel}>"

class ScenarioEvent(Base):
    """
    Model representing an explicit network scenario and its duration.
    """
    __tablename__ = "scenario_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ap_id = Column(String(50), index=True, nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    end_time = Column(DateTime, nullable=True)
    scenario_name = Column(String(100), nullable=False)
    root_cause = Column(String(100), nullable=True)
    recommendation_triggered = Column(String(50), nullable=True)
    client_topology_snapshot = Column(Text, nullable=True) # JSON snapshot of initial coords

    def __repr__(self):
        return f"<Telemetry ap_id={self.ap_id} timestamp={self.timestamp} channel={self.channel}>"


class Alert(Base):
    """
    Model representing anomalous network behavior alerts detected by the Change Detection Engine.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    ap_id = Column(String(50), index=True, nullable=False)
    alert_type = Column(String(50), nullable=False)  # e.g., "abnormal_interference", "retry_spike", "airtime_congestion"
    metric = Column(String(50), nullable=False)      # e.g., "noise_floor", "retry_rate", "airtime_utilization"
    value = Column(Float, nullable=False)            # Observed value during anomaly
    threshold = Column(Float, nullable=False)        # Threshold that was violated
    description = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Alert ap_id={self.ap_id} type={self.alert_type} metric={self.metric}>"


class Recommendation(Base):
    """
    Model representing Radio Resource Management (RRM) action recommendations generated by the Policy Engine.
    """
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
    ap_id = Column(String(50), index=True, nullable=False)
    action = Column(String(50), nullable=False)              # e.g., "CHANNEL_CHANGE", "POWER_ADJUST", "WIDTH_ADJUST"
    current_value = Column(String(50), nullable=False)       # Current setting (e.g., "6", "15dBm", "80MHz")
    recommended_value = Column(String(50), nullable=False)   # Recommended setting (e.g., "11", "12dBm", "40MHz")
    confidence = Column(Float, nullable=False)               # Policy rule score / confidence (0.0 to 1.0)
    root_cause = Column(String(100), nullable=True)          # Explicit root cause (e.g. "MICROWAVE_INTERFERENCE")
    reason = Column(String(1000), nullable=False)            # Descriptive reason explaining the recommendation (Multiline Causal Chain)
    expected_qoe_gain = Column(Float, nullable=True)         # Expected QoE increase if action is taken
    expected_retry_reduction = Column(Float, nullable=True)  # Expected retry rate reduction if action is taken

    def __repr__(self):
        return f"<Recommendation ap_id={self.ap_id} action={self.action} recommended_value={self.recommended_value}>"
