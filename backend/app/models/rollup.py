from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utc_now


class FacilityOperationalRollup(Base):
    __tablename__ = "facility_operational_rollups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True, nullable=False)
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    avg_occupancy_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    peak_occupancy_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    high_congestion_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_power_kw: Mapped[float | None] = mapped_column(Float)
    peak_power_kw: Mapped[float | None] = mapped_column(Float)
    avg_temperature: Mapped[float | None] = mapped_column(Float)
    avg_noise_level: Mapped[float | None] = mapped_column(Float)
    recommendation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    facility = relationship("Facility", back_populates="operational_rollups")
