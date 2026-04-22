from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.cv.detector import get_detector
from app.db.session import Base, get_db
from app.main import app
from app.models import Facility


def test_live_analyze_route_returns_transient_metrics(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("CV_BACKEND", "mock")
    get_settings.cache_clear()
    get_detector.cache_clear()

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    facility = Facility(name="Route Live Room", type="Library", location="1F", total_seats=30)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    facility_id = facility.id
    db.close()

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    image_path = tmp_path / "live-route.jpg"
    Image.new("RGB", (640, 360), (40, 80, 100)).save(image_path)

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        with image_path.open("rb") as image_file:
            response = client.post(
                "/api/live/analyze",
                data={"facility_id": str(facility_id), "persist": "false"},
                files={"file": ("live-route.jpg", image_file, "image/jpeg")},
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_detector.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["facility_id"] == facility_id
    assert payload["people_count"] >= 1
    assert payload["persisted"] is False
