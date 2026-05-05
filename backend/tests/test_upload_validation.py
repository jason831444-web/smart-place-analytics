from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.cv.detector import get_detector
from app.db.session import Base, get_db
from app.main import app
from app.models import Facility


def test_upload_analyze_rejects_invalid_content_type(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()
    get_detector.cache_clear()

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    facility = Facility(name="Upload Room", type="Library", location="1F", total_seats=20)
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

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.post(
            "/api/uploads/analyze",
            data={"facility_id": str(facility_id)},
            files={"file": ("not-image.txt", b"hello", "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_detector.cache_clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Only JPEG, PNG, and WebP images are supported"


def test_upload_analyze_rejects_invalid_image_bytes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()
    get_detector.cache_clear()

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    facility = Facility(name="Upload Room", type="Library", location="1F", total_seats=20)
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

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        response = client.post(
            "/api/uploads/analyze",
            data={"facility_id": str(facility_id)},
            files={"file": ("broken.jpg", b"not really a jpeg", "image/jpeg")},
        )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_detector.cache_clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is not a valid image"
