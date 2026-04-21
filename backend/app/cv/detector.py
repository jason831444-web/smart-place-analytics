from pathlib import Path

from app.core.config import get_settings
from app.cv.base import DetectionBox, DetectionResult, PersonDetector
from app.cv.mock_detector import MockPersonDetector


class YoloPersonDetector(PersonDetector):
    def __init__(self, model_name: str):
        from ultralytics import YOLO

        self.model_name = model_name
        self.model = YOLO(model_name)

    def detect(self, image_path: Path) -> DetectionResult:
        results = self.model(str(image_path), verbose=False)
        boxes: list[DetectionBox] = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls.item())
                label = self.model.names.get(cls_id, str(cls_id))
                if label != "person":
                    continue
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                boxes.append(
                    DetectionBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=float(box.conf.item()) if box.conf is not None else None,
                    )
                )
        return DetectionResult(people_count=len(boxes), boxes=boxes, backend="yolo", model_name=self.model_name)


def get_detector() -> PersonDetector:
    settings = get_settings()
    if settings.cv_backend.lower() == "yolo":
        try:
            return YoloPersonDetector(settings.yolo_model)
        except Exception:
            return MockPersonDetector()
    return MockPersonDetector()

