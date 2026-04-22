from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DetectionBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float | None = None
    label: str = "person"


@dataclass(frozen=True)
class DetectionResult:
    people_count: int
    boxes: list[DetectionBox]
    backend: str
    model_name: str
    fallback_reason: str | None = None


class PersonDetector:
    def detect(self, image_path: Path) -> DetectionResult:
        raise NotImplementedError


class DetectorConfigurationError(RuntimeError):
    pass
