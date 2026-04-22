from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Analysis, Facility, OccupancyLog, Upload
from app.schemas.analysis import LiveAnalysisRead
from app.services.analysis import analyze_image_for_facility, create_analysis_record
from app.services.storage import public_url_for_path, save_bytes_file


@dataclass(frozen=True)
class LivePersistenceDecision:
    should_persist: bool
    next_persist_after_seconds: int


def live_persistence_decision(db: Session, facility_id: int, persist_requested: bool, now: datetime | None = None) -> LivePersistenceDecision:
    if not persist_requested:
        return LivePersistenceDecision(should_persist=False, next_persist_after_seconds=0)

    settings = get_settings()
    interval = max(settings.live_persist_interval_seconds, 0)
    if interval == 0:
        return LivePersistenceDecision(should_persist=True, next_persist_after_seconds=0)

    now = now or datetime.utcnow()
    latest_timestamp = db.scalar(
        select(OccupancyLog.timestamp)
        .where(OccupancyLog.facility_id == facility_id)
        .order_by(desc(OccupancyLog.timestamp))
        .limit(1)
    )
    if not latest_timestamp:
        return LivePersistenceDecision(should_persist=True, next_persist_after_seconds=0)

    next_allowed_at = latest_timestamp + timedelta(seconds=interval)
    remaining = max(0, int((next_allowed_at - now).total_seconds()))
    return LivePersistenceDecision(should_persist=remaining == 0, next_persist_after_seconds=remaining)


def analyze_live_frame(
    db: Session,
    facility: Facility,
    frame_content: bytes,
    content_type: str,
    original_filename: str,
    persist_requested: bool,
) -> LiveAnalysisRead:
    decision = live_persistence_decision(db, facility.id, persist_requested)
    subdir = "uploads" if decision.should_persist else "live_frames"
    image_path = save_bytes_file(frame_content, content_type, subdir=subdir)
    analysis: Analysis | None = None
    upload: Upload | None = None
    remove_after_analysis = not decision.should_persist

    try:
        detection, congestion, annotated_path = analyze_image_for_facility(
            facility,
            image_path,
            annotate=decision.should_persist,
        )

        if decision.should_persist:
            upload = Upload(
                facility_id=facility.id,
                file_path=str(image_path),
                original_filename=original_filename,
            )
            db.add(upload)
            db.flush()
            analysis = create_analysis_record(db, facility, upload, congestion, annotated_path)

        return LiveAnalysisRead(
            facility_id=facility.id,
            people_count=congestion.people_count,
            occupied_seats=congestion.occupied_seats,
            available_seats=congestion.available_seats,
            occupancy_rate=congestion.occupancy_rate,
            congestion_level=congestion.congestion_level,
            congestion_score=congestion.congestion_score,
            detector_backend=detection.backend,
            detector_model=detection.model_name,
            persisted=analysis is not None,
            persistence_requested=persist_requested,
            next_persist_after_seconds=decision.next_persist_after_seconds,
            analysis_id=analysis.id if analysis else None,
            image_url=public_url_for_path(upload.file_path) if upload else None,
            annotated_image_url=public_url_for_path(analysis.annotated_image_path) if analysis else None,
            fallback_reason=detection.fallback_reason,
            created_at=analysis.created_at if analysis else datetime.utcnow(),
        )
    finally:
        if remove_after_analysis:
            try:
                Path(image_path).unlink(missing_ok=True)
            except OSError:
                pass
