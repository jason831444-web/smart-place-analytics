from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utc_now


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False, default="high_congestion")
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Operational alert")
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True, nullable=False)

    facility = relationship("Facility", back_populates="alerts")
