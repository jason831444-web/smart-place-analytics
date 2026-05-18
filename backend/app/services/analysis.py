from pathlib import Path
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.cv.annotate import annotate_image
from app.cv.detector import get_detector
from app.models import Analysis, Facility, OccupancyLog, Upload, User
from app.schemas.analysis import HistoryPoint
from app.services.congestion import calculate_congestion
from app.services.operations import create_occupancy_log
from app.services.storage import public_url_for_path
from app.utils.time import utc_now


def create_upload_record(db: Session, facility: Facility, path: Path, original_filename: str, user: User | None = None) -> Upload:
    upload = Upload(
        facility_id=facility.id,
        uploaded_by_user_id=user.id if user else None,
        file_path=str(path),
        original_filename=original_filename,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def analyze_image_for_facility(facility: Facility, image_path: Path, annotate: bool = True) -> tuple:
    detector = get_detector()
    detection = detector.detect(image_path)
    congestion = calculate_congestion(
        detection.people_count,
        facility.total_seats,
        facility.seat_usage_factor,
    )

    annotated_path = None
    if annotate and detection.boxes:
        annotated_path = get_settings().storage_dir / "annotated" / f"{uuid4().hex}.jpg"
        annotate_image(image_path, detection.boxes, annotated_path)

    return detection, congestion, annotated_path


def detection_confidence(detection) -> float | None:
    confidences = [box.confidence for box in detection.boxes if box.confidence is not None]
    if not confidences:
        return None
    return round(sum(confidences) / len(confidences), 4)


def create_analysis_record(
    db: Session,
    facility: Facility,
    upload: Upload,
    congestion,
    annotated_path: Path | None = None,
    *,
    detection=None,
    source_type: str = "image_upload",
) -> Analysis:
    analysis = Analysis(
        facility_id=facility.id,
        upload_id=upload.id,
        people_count=congestion.people_count,
        occupied_seats=congestion.occupied_seats,
        available_seats=congestion.available_seats,
        occupancy_rate=congestion.occupancy_rate,
        congestion_level=congestion.congestion_level,
        congestion_score=congestion.congestion_score,
        annotated_image_path=str(annotated_path) if annotated_path else None,
    )
    db.add(analysis)
    db.flush()
    create_occupancy_log(
        db,
        facility_id=facility.id,
        analysis_id=analysis.id,
        timestamp=analysis.created_at or utc_now(),
        people_count=analysis.people_count,
        occupied_seats=analysis.occupied_seats,
        available_seats=analysis.available_seats,
        occupancy_rate=analysis.occupancy_rate,
        congestion_score=analysis.congestion_score,
        congestion_level=analysis.congestion_level,
        confidence=detection_confidence(detection) if detection else None,
        source_type=source_type,
        image_path=upload.file_path,
        annotated_image_path=str(annotated_path) if annotated_path else None,
    )
    db.commit()
    db.refresh(analysis)
    return analysis


def run_analysis_for_upload(db: Session, upload: Upload) -> Analysis:
    facility = db.get(Facility, upload.facility_id)
    if not facility:
        raise ValueError("Facility not found for upload")

    detection, congestion, annotated_path = analyze_image_for_facility(facility, Path(upload.file_path), annotate=True)
    return create_analysis_record(
        db,
        facility,
        upload,
        congestion,
        annotated_path,
        detection=detection,
        source_type="image_upload",
    )


def analysis_to_dict(analysis: Analysis) -> dict:
    upload = analysis.upload
    return {
        "id": analysis.id,
        "facility_id": analysis.facility_id,
        "upload_id": analysis.upload_id,
        "people_count": analysis.people_count,
        "occupied_seats": analysis.occupied_seats,
        "available_seats": analysis.available_seats,
        "occupancy_rate": analysis.occupancy_rate,
        "congestion_level": analysis.congestion_level,
        "congestion_score": analysis.congestion_score,
        "annotated_image_path": analysis.annotated_image_path,
        "created_at": analysis.created_at,
        "image_url": public_url_for_path(upload.file_path) if upload else None,
        "annotated_image_url": public_url_for_path(analysis.annotated_image_path),
    }


def get_analysis(db: Session, analysis_id: int) -> Analysis | None:
    return db.get(Analysis, analysis_id)


def list_history(db: Session, facility_id: int, limit: int = 100) -> list[HistoryPoint]:
    logs = list(
        db.scalars(
            select(OccupancyLog)
            .where(OccupancyLog.facility_id == facility_id)
            .order_by(desc(OccupancyLog.timestamp))
            .limit(limit)
        ).all()
    )
    return [
        HistoryPoint(
            timestamp=log.timestamp,
            people_count=log.people_count,
            occupied_seats=log.occupied_seats,
            available_seats=log.available_seats,
            occupancy_rate=log.occupancy_rate,
            congestion_score=log.congestion_score,
            congestion_level=log.congestion_level,
        )
        for log in logs
    ]
