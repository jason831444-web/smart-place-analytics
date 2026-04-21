from app.services.congestion import calculate_congestion, congestion_level_for_rate


def test_congestion_clamps_people_to_capacity() -> None:
    result = calculate_congestion(12, 10)

    assert result.people_count == 12
    assert result.occupied_seats == 10
    assert result.available_seats == 0
    assert result.occupancy_rate == 1
    assert result.congestion_score == 100
    assert result.congestion_level == "High"


def test_congestion_handles_zero_seats_defensively() -> None:
    result = calculate_congestion(8, 0)

    assert result.occupied_seats == 0
    assert result.available_seats == 0
    assert result.occupancy_rate == 0
    assert result.congestion_score == 0
    assert result.congestion_level == "Low"


def test_level_boundaries() -> None:
    assert congestion_level_for_rate(0.30) == "Low"
    assert congestion_level_for_rate(0.31) == "Medium"
    assert congestion_level_for_rate(0.70) == "Medium"
    assert congestion_level_for_rate(0.71) == "High"

