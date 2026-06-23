from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class TelemetryBase(BaseModel):
    ap_id: str
    channel: int
    rssi: float
    snr: float
    noise_floor: float
    airtime_utilization: float
    retry_rate: float
    client_count: int
    qoe_score: Optional[float] = None
    qoe_category: Optional[str] = None
    interference_type: Optional[str] = None
    distance: Optional[float] = None
    max_distance: Optional[float] = None
    closest_client: Optional[float] = None
    furthest_client: Optional[float] = None
    freq_mhz: Optional[float] = None
    tx_power: Optional[float] = None
    wall_count: Optional[int] = None
    wall_loss: Optional[float] = None
    scenario_name: Optional[str] = None

class ScenarioEventBase(BaseModel):
    ap_id: str
    scenario_name: str
    root_cause: Optional[str] = None
    recommendation_triggered: Optional[str] = None
    client_topology_snapshot: Optional[str] = None

class ScenarioEventResponse(ScenarioEventBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TelemetryCreate(TelemetryBase):
    pass

class TelemetryResponse(TelemetryBase):
    id: int
    timestamp: datetime

    # Pydantic v2 configuration to allow parsing from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    ap_id: str
    alert_type: str
    metric: str
    value: float
    threshold: float
    description: str

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationBase(BaseModel):
    ap_id: str
    action: str
    current_value: str
    recommended_value: str
    confidence: float
    root_cause: Optional[str] = None
    reason: str
    expected_qoe_gain: Optional[float] = None

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationResponse(RecommendationBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class APSummary(BaseModel):
    """Summarized health and configuration payload for a specific Access Point."""
    ap_id: str
    channel: int
    client_count: int
    status: str  # e.g., "Healthy", "Warning", "Critical"
    active_alert_count: int
    recent_recommendation: Optional[str] = None
