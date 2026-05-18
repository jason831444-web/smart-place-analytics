from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OccupancyLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facility_id: int
    analysis_id: int | None = None
    timestamp: datetime
    people_count: int
    occupied_seats: int
    available_seats: int
    occupancy_rate: float
    congestion_score: float
    congestion_level: str
    confidence: float | None = None
    source_type: str
    image_path: str | None = None
    annotated_image_path: str | None = None
    image_url: str | None = None
    annotated_image_url: str | None = None
    created_at: datetime


class LatestStatusRead(BaseModel):
    facility_id: int
    timestamp: datetime | None = None
    people_count: int = 0
    occupied_seats: int = 0
    available_seats: int = 0
    occupancy_rate: float = 0
    congestion_score: float = 0
    congestion_level: str = "Low"
    confidence: float | None = None
    source_type: str | None = None
    analysis_id: int | None = None
    image_url: str | None = None
    annotated_image_url: str | None = None


class FacilitySummaryRead(BaseModel):
    facility_id: int
    latest_occupancy_rate: float = 0
    average_occupancy_rate: float = 0
    peak_occupancy_rate: float = 0
    high_congestion_events: int = 0
    most_recent_timestamp: datetime | None = None
    latest_people_count: int = 0
    samples: int = 0


class SensorLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facility_id: int
    timestamp: datetime
    temperature: float
    humidity: float
    power_kw: float
    door_count: int
    noise_level: float
    source_type: str
    created_at: datetime


class SensorSummaryRead(BaseModel):
    facility_id: int
    latest_temperature: float | None = None
    latest_humidity: float | None = None
    latest_power_kw: float | None = None
    latest_door_count: int | None = None
    latest_noise_level: float | None = None
    average_temperature: float = 0
    average_humidity: float = 0
    average_power_kw: float = 0
    total_door_count: int = 0
    average_noise_level: float = 0
    most_recent_timestamp: datetime | None = None
    samples: int = 0


class FacilityOperationalRollupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facility_id: int
    timestamp: datetime
    window_minutes: int
    avg_occupancy_rate: float
    peak_occupancy_rate: float
    high_congestion_events: int
    avg_power_kw: float | None = None
    peak_power_kw: float | None = None
    avg_temperature: float | None = None
    avg_noise_level: float | None = None
    recommendation_count: int
    created_at: datetime


class ForecastRead(BaseModel):
    facility_id: int
    window_minutes: int
    predicted_occupancy_rate: float
    predicted_congestion_level: str
    confidence: float
    method: str
    explanation: str
    generated_at: datetime


class RecommendationRead(BaseModel):
    recommendation_type: str
    severity: str
    title: str
    message: str
    evidence: list[str]
    created_at: datetime


class JobStatusRead(BaseModel):
    latest_sensor_log_at: datetime | None = None
    latest_rollup_at: datetime | None = None
    total_sensor_logs: int = 0
    total_rollups: int = 0
    facilities_with_recent_activity: int = 0
    generated_at: datetime
