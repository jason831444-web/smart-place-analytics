from pathlib import Path
from functools import lru_cache
import logging

from app.core.config import get_settings
from app.cv.base import DetectionBox, DetectionResult, DetectorConfigurationError, PersonDetector
from app.cv.mock_detector import MockPersonDetector

logger = logging.getLogger(__name__)


class YoloPersonDetector(PersonDetector):
    def __init__(self, model_name: str, confidence_threshold: float = 0.25, device: str | None = None):
        from ultralytics import YOLO

        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = YOLO(model_name)

    def detect(self, image_path: Path) -> DetectionResult:
        predict_kwargs = {"verbose": False, "conf": self.confidence_threshold}
        if self.device:
            predict_kwargs["device"] = self.device
        results = self.model(str(image_path), **predict_kwargs)
        boxes: list[DetectionBox] = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls.item())
                names = getattr(result, "names", None) or getattr(self.model, "names", {})
                label = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(cls_id)
                if label != "person":
                    continue
                confidence = float(box.conf.item()) if box.conf is not None else None
                if confidence is not None and confidence < self.confidence_threshold:
                    continue
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                boxes.append(
                    DetectionBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=confidence,
                    )
                )
        return DetectionResult(people_count=len(boxes), boxes=boxes, backend="yolo", model_name=self.model_name)


@lru_cache(maxsize=1)
def get_detector() -> PersonDetector:
    settings = get_settings()
    backend = settings.cv_backend.strip().lower()

    if backend == "mock":
        return MockPersonDetector()

    if backend == "yolo":
        try:
            return YoloPersonDetector(
                model_name=settings.yolo_model,
                confidence_threshold=settings.yolo_confidence_threshold,
                device=settings.yolo_device,
            )
        except Exception as exc:
            message = f"YOLO detector unavailable: {exc}"
            if settings.yolo_fallback_to_mock:
                logger.warning("%s. Falling back to mock detector.", message)
                return MockPersonDetector(fallback_reason=message)
            raise DetectorConfigurationError(message) from exc

    raise DetectorConfigurationError(f"Unsupported CV_BACKEND '{settings.cv_backend}'. Expected 'mock' or 'yolo'.")
