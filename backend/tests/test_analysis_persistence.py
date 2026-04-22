from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.cv.detector import get_detector
from app.db.session import Base
from app.models import Facility, OccupancyLog, Upload
from app.services.analysis import run_analysis_for_upload


def test_run_analysis_persists_analysis_and_occupancy_log(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CV_BACKEND", "mock")
    get_settings.cache_clear()
    get_detector.cache_clear()

    image_path = tmp_path / "analysis-input.jpg"
    Image.new("RGB", (640, 360), (22, 44, 66)).save(image_path)

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    facility = Facility(name="Test Library", type="Library", location="1F", total_seats=20)
    db.add(facility)
    db.flush()
    upload = Upload(facility_id=facility.id, file_path=str(image_path), original_filename=image_path.name)
    db.add(upload)
    db.commit()
    db.refresh(upload)

    analysis = run_analysis_for_upload(db, upload)
    log = db.scalar(select(OccupancyLog).where(OccupancyLog.analysis_id == analysis.id))

    assert analysis.id is not None
    assert analysis.people_count >= 1
    assert analysis.occupied_seats == min(analysis.people_count, facility.total_seats)
    assert analysis.annotated_image_path is not None
    assert log is not None
    assert log.people_count == analysis.people_count

    get_settings.cache_clear()
    get_detector.cache_clear()
