import pytest

from app.core.config import get_settings
from app.cv.base import DetectorConfigurationError
from app.cv.detector import get_detector
from app.cv.mock_detector import MockPersonDetector


def reset_config() -> None:
    get_settings.cache_clear()
    get_detector.cache_clear()


def test_mock_backend_selects_mock_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CV_BACKEND", "mock")
    reset_config()

    detector = get_detector()

    assert isinstance(detector, MockPersonDetector)
    reset_config()


def test_invalid_backend_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CV_BACKEND", "not-real")
    reset_config()

    with pytest.raises(DetectorConfigurationError, match="Unsupported CV_BACKEND"):
        get_detector()
    reset_config()


def test_yolo_backend_falls_back_to_mock_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CV_BACKEND", "yolo")
    monkeypatch.setenv("YOLO_MODEL", "definitely-not-a-real-local-model.pt")
    monkeypatch.setenv("YOLO_FALLBACK_TO_MOCK", "true")
    reset_config()

    detector = get_detector()

    assert isinstance(detector, MockPersonDetector)
    assert detector.fallback_reason is not None
    reset_config()
