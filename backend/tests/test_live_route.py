from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.cv.detector import get_detector
from app.db.session import Base, get_db
from app.main import app
from app.models import Facility, User


def test_live_analyze_route_requires_admin_auth(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("CV_BACKEND", "mock")
    get_settings.cache_clear()
    get_detector.cache_clear()

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    facility = Facility(name="Route Live Room", type="Library", location="1F", total_seats=30)
    user = User(email="viewer@example.com", password_hash=hash_password("password123"), role="viewer")
    db.add_all([facility, user])
    db.commit()
    db.refresh(facility)
    db.refresh(user)
    facility_id = facility.id
    user_id = user.id
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
            unauthorized_response = client.post(
                "/api/live/analyze",
                data={"facility_id": str(facility_id), "persist": "false"},
                files={"file": ("live-route.jpg", image_file, "image/jpeg")},
            )
        with image_path.open("rb") as image_file:
            forbidden_response = client.post(
                "/api/live/analyze",
                data={"facility_id": str(facility_id), "persist": "false"},
                files={"file": ("live-route.jpg", image_file, "image/jpeg")},
                headers={"Authorization": f"Bearer {create_access_token(str(user_id))}"},
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_detector.cache_clear()

    assert unauthorized_response.status_code == 401
    assert forbidden_response.status_code == 403


def test_live_analyze_route_returns_transient_metrics_for_admin(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("CV_BACKEND", "mock")
    get_settings.cache_clear()
    get_detector.cache_clear()

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    facility = Facility(name="Route Live Room", type="Library", location="1F", total_seats=30)
    admin = User(email="admin@example.com", password_hash=hash_password("password123"), role="admin")
    db.add_all([facility, admin])
    db.commit()
    db.refresh(facility)
    db.refresh(admin)
    facility_id = facility.id
    admin_token = create_access_token(str(admin.id))
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
                headers={"Authorization": f"Bearer {admin_token}"},
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
