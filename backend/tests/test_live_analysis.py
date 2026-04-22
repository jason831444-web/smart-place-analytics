from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.cv.detector import get_detector
from app.db.session import Base
from app.models import Analysis, Facility, OccupancyLog, Upload
from app.services.live import analyze_live_frame, live_persistence_decision


def make_image_bytes(path: Path) -> bytes:
    Image.new("RGB", (640, 360), (30, 70, 90)).save(path)
    return path.read_bytes()


def make_db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def reset_settings() -> None:
    get_settings.cache_clear()
    get_detector.cache_clear()


def test_live_persistence_decision_respects_interval(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("LIVE_PERSIST_INTERVAL_SECONDS", "60")
    reset_settings()
    db = make_db()
    facility = Facility(name="Live Room", type="Library", location="1F", total_seats=20)
    db.add(facility)
    db.flush()
    upload = Upload(facility_id=facility.id, file_path="frame.jpg", original_filename="frame.jpg")
    db.add(upload)
    db.flush()
    analysis = Analysis(
        facility_id=facility.id,
        upload_id=upload.id,
        people_count=5,
        occupied_seats=5,
        available_seats=15,
        occupancy_rate=0.25,
        congestion_level="Low",
        congestion_score=25,
        created_at=datetime(2026, 4, 22, 12, 0, 0),
    )
    db.add(analysis)
    db.flush()
    db.add(
        OccupancyLog(
            facility_id=facility.id,
            analysis_id=analysis.id,
            timestamp=datetime(2026, 4, 22, 12, 0, 0),
            people_count=5,
            occupied_seats=5,
            available_seats=15,
            occupancy_rate=0.25,
            congestion_score=25,
            congestion_level="Low",
        )
    )
    db.commit()

    too_soon = live_persistence_decision(db, facility.id, True, now=datetime(2026, 4, 22, 12, 0, 20))
    later = live_persistence_decision(db, facility.id, True, now=datetime(2026, 4, 22, 12, 1, 1))

    assert too_soon.should_persist is False
    assert too_soon.next_persist_after_seconds == 40
    assert later.should_persist is True
    reset_settings()


def test_live_frame_can_run_without_persisting(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("CV_BACKEND", "mock")
    reset_settings()
    db = make_db()
    facility = Facility(name="Live Room", type="Library", location="1F", total_seats=20)
    db.add(facility)
    db.commit()
    db.refresh(facility)

    result = analyze_live_frame(
        db=db,
        facility=facility,
        frame_content=make_image_bytes(tmp_path / "frame.jpg"),
        content_type="image/jpeg",
        original_filename="frame.jpg",
        persist_requested=False,
    )

    assert result.persisted is False
    assert result.people_count >= 1
    assert db.scalar(select(Analysis)) is None
    assert list((tmp_path / "storage" / "live_frames").glob("*")) == []
    reset_settings()


def test_live_frame_persists_when_interval_allows(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("CV_BACKEND", "mock")
    reset_settings()
    db = make_db()
    facility = Facility(name="Live Room", type="Library", location="1F", total_seats=20)
    db.add(facility)
    db.commit()
    db.refresh(facility)

    result = analyze_live_frame(
        db=db,
        facility=facility,
        frame_content=make_image_bytes(tmp_path / "frame.jpg"),
        content_type="image/jpeg",
        original_filename="frame.jpg",
        persist_requested=True,
    )

    assert result.persisted is True
    assert result.analysis_id is not None
    assert result.image_url is not None
    assert db.scalar(select(Analysis).where(Analysis.id == result.analysis_id)) is not None
    assert db.scalar(select(OccupancyLog).where(OccupancyLog.analysis_id == result.analysis_id)) is not None
    reset_settings()
