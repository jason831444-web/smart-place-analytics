from datetime import datetime

from pydantic import BaseModel


class FacilityMetric(BaseModel):
    facility_id: int
    facility_name: str
    average_occupancy_rate: float
    average_congestion_score: float
    latest_congestion_level: str | None = None
    analyses_count: int


class PeakHourMetric(BaseModel):
    hour: int
    average_occupancy_rate: float
    average_congestion_score: float
    samples: int


class DailyTrendPoint(BaseModel):
    date: str
    average_occupancy_rate: float
    average_congestion_score: float
    samples: int


class RecentActivity(BaseModel):
    analysis_id: int
    facility_id: int
    facility_name: str
    people_count: int
    occupancy_rate: float
    congestion_level: str
    created_at: datetime


class AnalyticsOverview(BaseModel):
    facilities_count: int
    analyses_count: int
    uploads_count: int
    average_occupancy_rate: float
    average_congestion_score: float
    busiest_facilities: list[FacilityMetric]
    peak_hours: list[PeakHourMetric]
    recent_activity: list[RecentActivity]


class FacilityAnalytics(BaseModel):
    facility_id: int
    average_occupancy_rate: float
    average_congestion_score: float
    peak_hours: list[PeakHourMetric]
    daily_trend: list[DailyTrendPoint]
    recent_activity: list[RecentActivity]

