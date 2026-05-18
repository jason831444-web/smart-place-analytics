from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import OccupancyLog
from app.schemas.operations import RecommendationRead
from app.services.forecasting import forecast_response
from app.services.operations import facility_summary, latest_status
from app.services.sensors import sensor_summary


def build_recommendations(db: Session, facility_id: int) -> list[RecommendationRead]:
    created_at = datetime.utcnow()
    status = latest_status(db, facility_id)
    forecast = forecast_response(db, facility_id)
    sensors = sensor_summary(db, facility_id)
    summary = facility_summary(db, facility_id)
    recommendations: list[RecommendationRead] = []

    if status.occupancy_rate > 0.85:
        recommendations.append(
            RecommendationRead(
                recommendation_type="occupancy_redirect",
                severity="high",
                title="Redirect traffic to alternate spaces",
                message="Current occupancy is above 85%. Route incoming users to lower-utilization facilities to reduce congestion.",
                evidence=[
                    f"Current occupancy rate: {round(status.occupancy_rate * 100)}%",
                    f"Current congestion level: {status.congestion_level}",
                ],
                created_at=created_at,
            )
        )

    if forecast.predicted_occupancy_rate > 0.90:
        recommendations.append(
            RecommendationRead(
                recommendation_type="overflow_capacity",
                severity="high",
                title="Prepare overflow capacity",
                message="Near-term occupancy is forecast to exceed 90%. Consider opening overflow seating or adjusting routing rules.",
                evidence=[
                    f"Forecast method: {forecast.method}",
                    f"Predicted occupancy rate: {round(forecast.predicted_occupancy_rate * 100)}%",
                ],
                created_at=created_at,
            )
        )

    if sensors.samples and sensors.latest_power_kw is not None and sensors.latest_power_kw > 12 and status.occupancy_rate < 0.35:
        recommendations.append(
            RecommendationRead(
                recommendation_type="energy_optimization",
                severity="medium",
                title="Reduce lighting or HVAC load",
                message="Power draw is elevated while occupancy is low. Scale back lighting, HVAC, or auxiliary equipment for this facility.",
                evidence=[
                    f"Latest power draw: {round(sensors.latest_power_kw, 2)} kW",
                    f"Current occupancy rate: {round(status.occupancy_rate * 100)}%",
                ],
                created_at=created_at,
            )
        )

    repeated_high = db.scalar(
        select(func.count(OccupancyLog.id)).where(
            OccupancyLog.facility_id == facility_id,
            OccupancyLog.congestion_level == "High",
        )
    ) or 0
    if repeated_high >= 3:
        recommendations.append(
            RecommendationRead(
                recommendation_type="staffing_schedule_adjustment",
                severity="medium",
                title="Review staffing and schedule patterns",
                message="High congestion is recurring often enough to justify a schedule, staffing, or access-policy adjustment.",
                evidence=[
                    f"Recorded high-congestion events: {int(repeated_high)}",
                    f"Peak occupancy rate: {round(summary.peak_occupancy_rate * 100)}%",
                ],
                created_at=created_at,
            )
        )

    if not recommendations:
        recommendations.append(
            RecommendationRead(
                recommendation_type="stable_operations",
                severity="low",
                title="Operations are stable",
                message="No urgent facility optimization action is recommended right now. Continue monitoring occupancy, energy, and traffic patterns.",
                evidence=[
                    f"Current occupancy rate: {round(status.occupancy_rate * 100)}%",
                    f"Forecast occupancy rate: {round(forecast.predicted_occupancy_rate * 100)}%",
                ],
                created_at=created_at,
            )
        )

    return recommendations
