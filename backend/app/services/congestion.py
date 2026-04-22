from dataclasses import dataclass


@dataclass(frozen=True)
class CongestionResult:
    people_count: int
    occupied_seats: int
    available_seats: int
    occupancy_rate: float
    congestion_level: str
    congestion_score: float


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def congestion_level_for_rate(rate: float) -> str:
    if rate <= 0.30:
        return "Low"
    if rate <= 0.70:
        return "Medium"
    return "High"


def calculate_congestion(
    people_count: int,
    total_seats: int,
    seat_usage_factor: float = 1.0,
) -> CongestionResult:
    safe_people = max(int(people_count), 0)
    safe_seats = max(int(total_seats), 0)
    safe_factor = max(float(seat_usage_factor), 0.0)

    if safe_seats == 0:
        occupied = 0
        available = 0
        rate = 0.0
    else:
        estimated_occupied = round(safe_people * safe_factor)
        occupied = min(max(estimated_occupied, 0), safe_seats)
        available = max(safe_seats - occupied, 0)
        rate = clamp(occupied / safe_seats, 0.0, 1.0)

    score = round(clamp(rate * 100, 0.0, 100.0), 2)
    return CongestionResult(
        people_count=safe_people,
        occupied_seats=occupied,
        available_seats=available,
        occupancy_rate=round(rate, 4),
        congestion_level=congestion_level_for_rate(rate),
        congestion_score=score,
    )