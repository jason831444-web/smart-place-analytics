from datetime import datetime

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float | None = None
    label: str = "person"


class UploadRead(BaseModel):
    id: int
    facility_id: int
    uploaded_by_user_id: int | None
    file_path: str
    original_filename: str
    uploaded_at: datetime
    url: str | None = None

    class Config:
        from_attributes = True


class AnalysisRead(BaseModel):
    id: int
    facility_id: int
    upload_id: int
    people_count: int
    occupied_seats: int
    available_seats: int
    occupancy_rate: float
    congestion_level: str
    congestion_score: float
    annotated_image_path: str | None
    created_at: datetime
    image_url: str | None = None
    annotated_image_url: str | None = None

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    upload_id: int


class HistoryPoint(BaseModel):
    timestamp: datetime
    people_count: int
    occupied_seats: int
    available_seats: int
    occupancy_rate: float
    congestion_score: float
    congestion_level: str


class LiveAnalysisRead(BaseModel):
    facility_id: int
    people_count: int
    occupied_seats: int
    available_seats: int
    occupancy_rate: float
    congestion_level: str
    congestion_score: float
    detector_backend: str
    detector_model: str
    persisted: bool
    persistence_requested: bool
    next_persist_after_seconds: int
    analysis_id: int | None = None
    image_url: str | None = None
    annotated_image_url: str | None = None
    fallback_reason: str | None = None
    created_at: datetime
