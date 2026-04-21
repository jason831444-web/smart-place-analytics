from datetime import datetime

from pydantic import BaseModel, Field


class FacilityBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    type: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=255)
    description: str | None = None
    total_seats: int = Field(ge=0)
    image_url: str | None = None


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    type: str | None = Field(default=None, min_length=2, max_length=100)
    location: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    total_seats: int | None = Field(default=None, ge=0)
    image_url: str | None = None


class FacilityRead(FacilityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FacilityStatus(BaseModel):
    facility: FacilityRead
    people_count: int = 0
    occupied_seats: int = 0
    available_seats: int = 0
    occupancy_rate: float = 0
    congestion_level: str = "Low"
    congestion_score: float = 0
    latest_analysis_id: int | None = None
    latest_analysis_at: datetime | None = None

