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
    reason: str

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
