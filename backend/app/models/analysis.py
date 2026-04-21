from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    upload_id: Mapped[int] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=False)
    people_count: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy_rate: Mapped[float] = mapped_column(Float, nullable=False)
    congestion_level: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    congestion_score: Mapped[float] = mapped_column(Float, nullable=False)
    annotated_image_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    facility = relationship("Facility", back_populates="analyses")
    upload = relationship("Upload", back_populates="analysis")
    occupancy_log = relationship("OccupancyLog", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class OccupancyLog(Base):
    __tablename__ = "occupancy_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    people_count: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy_rate: Mapped[float] = mapped_column(Float, nullable=False)
    congestion_score: Mapped[float] = mapped_column(Float, nullable=False)
    congestion_level: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    facility = relationship("Facility", back_populates="occupancy_logs")
    analysis = relationship("Analysis", back_populates="occupancy_log")

