from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.analysis import HistoryPoint
from app.schemas.facility import FacilityRead, FacilityStatus
from app.schemas.operations import (
    FacilitySummaryRead,
    FacilityOperationalRollupRead,
    ForecastRead,
    LatestStatusRead,
    OccupancyLogRead,
    RecommendationRead,
    SensorLogRead,
    SensorSummaryRead,
)
from app.services.analysis import list_history
from app.services.facilities import facility_status, get_facility_or_none, list_facilities
from app.services.forecasting import forecast_response
from app.services.operations import facility_summary, latest_status, list_occupancy_logs, serialize_occupancy_log
from app.services.recommendations import build_recommendations
from app.services.rollups import compute_and_store_rollup, latest_rollup, list_rollups, serialize_rollup
from app.services.sensors import list_sensor_logs, sensor_summary

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityStatus])
def facilities(db: Session = Depends(get_db)) -> list[FacilityStatus]:
    return [facility_status(db, facility) for facility in list_facilities(db)]


@router.get("/{facility_id}", response_model=FacilityRead)
def facility_detail(facility_id: int, db: Session = Depends(get_db)) -> FacilityRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@router.get("/{facility_id}/status", response_model=FacilityStatus)
def status(facility_id: int, db: Session = Depends(get_db)) -> FacilityStatus:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility_status(db, facility)


@router.get("/{facility_id}/history", response_model=list[HistoryPoint])
def history(facility_id: int, limit: int = 100, db: Session = Depends(get_db)) -> list[HistoryPoint]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return list_history(db, facility_id, limit=min(limit, 500))


@router.get("/{facility_id}/occupancy-logs", response_model=list[OccupancyLogRead])
def occupancy_logs(facility_id: int, limit: int = 200, db: Session = Depends(get_db)) -> list[OccupancyLogRead]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return [serialize_occupancy_log(log) for log in list_occupancy_logs(db, facility_id, limit=min(limit, 500))]


@router.get("/{facility_id}/latest-status", response_model=LatestStatusRead)
def latest_status_route(facility_id: int, db: Session = Depends(get_db)) -> LatestStatusRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return latest_status(db, facility_id)


@router.get("/{facility_id}/summary", response_model=FacilitySummaryRead)
def summary_route(facility_id: int, db: Session = Depends(get_db)) -> FacilitySummaryRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility_summary(db, facility_id)


@router.get("/{facility_id}/sensor-logs", response_model=list[SensorLogRead])
def sensor_logs_route(facility_id: int, limit: int = 200, db: Session = Depends(get_db)) -> list[SensorLogRead]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return list_sensor_logs(db, facility_id, limit=min(limit, 500))


@router.get("/{facility_id}/sensor-summary", response_model=SensorSummaryRead)
def sensor_summary_route(facility_id: int, db: Session = Depends(get_db)) -> SensorSummaryRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return sensor_summary(db, facility_id)


@router.get("/{facility_id}/forecast", response_model=ForecastRead)
def forecast_route(facility_id: int, window_minutes: int = 60, db: Session = Depends(get_db)) -> ForecastRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return forecast_response(db, facility_id, window_minutes=max(15, min(window_minutes, 240)))


@router.get("/{facility_id}/recommendations", response_model=list[RecommendationRead])
def recommendations_route(facility_id: int, db: Session = Depends(get_db)) -> list[RecommendationRead]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return build_recommendations(db, facility_id)


@router.post("/{facility_id}/rollups/compute", response_model=FacilityOperationalRollupRead)
def compute_rollup_route(
    facility_id: int,
    window_minutes: int = 60,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FacilityOperationalRollupRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    rollup = compute_and_store_rollup(db, facility_id, window_minutes=max(15, min(window_minutes, 720)))
    db.commit()
    db.refresh(rollup)
    return serialize_rollup(rollup)


@router.get("/{facility_id}/rollups", response_model=list[FacilityOperationalRollupRead])
def rollups_route(facility_id: int, limit: int = 100, db: Session = Depends(get_db)) -> list[FacilityOperationalRollupRead]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return [serialize_rollup(item) for item in list_rollups(db, facility_id, limit=min(limit, 250))]


@router.get("/{facility_id}/rollups/latest", response_model=FacilityOperationalRollupRead | None)
def latest_rollup_route(facility_id: int, db: Session = Depends(get_db)) -> FacilityOperationalRollupRead | None:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    rollup = latest_rollup(db, facility_id)
    return serialize_rollup(rollup) if rollup else None
