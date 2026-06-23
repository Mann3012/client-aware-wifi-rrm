import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.connection import get_db
from src.database.models import Telemetry, Alert, Recommendation, ScenarioEvent
from src.api.schemas import TelemetryResponse, AlertResponse, RecommendationResponse, APSummary, ScenarioEventResponse

router = APIRouter()

@router.get("/telemetry", response_model=List[TelemetryResponse])
def get_telemetry(
    ap_id: Optional[str] = Query(None, description="Filter telemetry by Access Point ID"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of returned records"),
    db: Session = Depends(get_db)
):
    """Retrieves chronological Access Point telemetry from the database."""
    query = db.query(Telemetry)
    if ap_id:
        query = query.filter(Telemetry.ap_id == ap_id)
    
    # Return latest records ordered by timestamp descending, but return them sorted chronologically
    records = query.order_by(Telemetry.timestamp.desc()).limit(limit).all()
    records.reverse()
    return records


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    ap_id: Optional[str] = Query(None, description="Filter alerts by Access Point ID"),
    active_only: bool = Query(False, description="Only return alerts from the last 30 minutes"),
    limit: int = Query(50, ge=1, le=500, description="Limit the number of returned records"),
    db: Session = Depends(get_db)
):
    """Retrieves detected network anomaly alerts from the database."""
    query = db.query(Alert)
    if ap_id:
        query = query.filter(Alert.ap_id == ap_id)
    
    if active_only:
        threshold_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        query = query.filter(Alert.timestamp >= threshold_time)
        
    records = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    return records


@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(
    ap_id: Optional[str] = Query(None, description="Filter recommendations by Access Point ID"),
    limit: int = Query(50, ge=1, le=500, description="Limit the number of returned records"),
    db: Session = Depends(get_db)
):
    """Retrieves RRM channel, power, and width optimization recommendations from the database."""
    query = db.query(Recommendation)
    if ap_id:
        query = query.filter(Recommendation.ap_id == ap_id)
        
    records = query.order_by(Recommendation.timestamp.desc()).limit(limit).all()
    return records


@router.get("/ap-status", response_model=List[APSummary])
def get_ap_status(db: Session = Depends(get_db)):
    """Computes a live status and health summary scorecard for all Access Points in the database."""
    # Find all unique AP IDs
    ap_ids = db.query(Telemetry.ap_id).distinct().all()
    ap_ids = [ap[0] for ap in ap_ids]

    summary_list = []
    for ap_id in ap_ids:
        # Get latest telemetry
        latest_telemetry = (
            db.query(Telemetry)
            .filter(Telemetry.ap_id == ap_id)
            .order_by(Telemetry.timestamp.desc())
            .first()
        )
        if not latest_telemetry:
            continue

        # Count active alerts in the last 30 minutes
        thirty_mins_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        active_alerts = (
            db.query(Alert)
            .filter(Alert.ap_id == ap_id, Alert.timestamp >= thirty_mins_ago)
            .all()
        )
        alert_count = len(active_alerts)

        # Get latest recommendation
        latest_rec = (
            db.query(Recommendation)
            .filter(Recommendation.ap_id == ap_id)
            .order_by(Recommendation.timestamp.desc())
            .first()
        )
        rec_str = f"{latest_rec.action} to {latest_rec.recommended_value}" if latest_rec else "None"

        # Determine Health Status
        alert_types = {a.alert_type for a in active_alerts}
        if "abnormal_interference" in alert_types:
            status = "Critical"
        elif alert_count > 0:
            status = "Warning"
        else:
            status = "Healthy"

        summary_list.append(
            APSummary(
                ap_id=ap_id,
                channel=latest_telemetry.channel,
                client_count=latest_telemetry.client_count,
                status=status,
                active_alert_count=alert_count,
                recent_recommendation=rec_str
            )
        )
    
    return summary_list


@router.post("/simulator/trigger")
def trigger_simulator(db: Session = Depends(get_db)):
    """
    Manually triggers a simulation step.
    Useful for dashboard controls to inject data instantly during demonstrations.
    """
    from src.api.main import app_simulator
    if not app_simulator:
        raise HTTPException(status_code=503, detail="Simulator is not active or initialized.")
    try:
        app_simulator.step()
        return {"status": "Success", "message": "Simulation step triggered successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to step simulator: {e}")

@router.get("/scenario/history", response_model=List[ScenarioEventResponse])
def get_scenario_history(
    ap_id: Optional[str] = Query(None, description="Filter history by AP ID"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(ScenarioEvent)
    if ap_id:
        query = query.filter(ScenarioEvent.ap_id == ap_id)
    records = query.order_by(ScenarioEvent.start_time.desc()).limit(limit).all()
    return records

@router.post("/scenario/set")
def set_scenario(ap_id: str = Query(...), scenario_name: str = Query(...)):
    from src.api.main import app_simulator
    if not app_simulator:
        raise HTTPException(status_code=503, detail="Simulator is not active.")
    app_simulator.force_scenario(ap_id, scenario_name)
    app_simulator.step() # Instantly apply it
    return {"status": "Success", "message": f"Scenario {scenario_name} forced on {ap_id}"}
