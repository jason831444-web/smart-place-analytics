from pathlib import Path

from PIL import Image

from app.cv.base import DetectionBox, DetectionResult, PersonDetector


class MockPersonDetector(PersonDetector):
    """Deterministic fallback detector so the app can run without ML weights."""

    def detect(self, image_path: Path) -> DetectionResult:
        with Image.open(image_path) as image:
            width, height = image.size
        seed = sum(image_path.name.encode("utf-8")) + width + height
        count = max(1, min(8, seed % 9))
        boxes: list[DetectionBox] = []
        box_w = max(width * 0.08, 32)
        box_h = max(height * 0.20, 48)
        for index in range(count):
            x = ((index + 1) * width / (count + 1)) - box_w / 2
            y = height * (0.38 + 0.08 * (index % 3))
            boxes.append(
                DetectionBox(
                    x1=max(0, x),
                    y1=max(0, y),
                    x2=min(width, x + box_w),
                    y2=min(height, y + box_h),
                    confidence=0.55,
                )
            )
        return DetectionResult(people_count=count, boxes=boxes, backend="mock", model_name="deterministic-layout")

