import polars as pl
import pytest

from clutch_x.etl.pressure_index import compute_pressure_index


def test_pressure_index_scores_chase_collapse_and_death_pressure() -> None:
    deliveries = pl.DataFrame(
        {
            "match_id": [1, 1, 2],
            "innings": [1, 1, 2],
            "match_format": ["T20I"] * 3,
            "season": ["2024"] * 3,
            "overid": [5, 20, 20],
            "pre_delivery_wickets": [3, 0, 3],
            "balls_remaining": [90, 6, 6],
            "scheduled_legal_balls": [120, 120, 120],
            "runs_required": [None, None, 12],
            "knock_out": [False, False, True],
            "delivery_total_runs": [1, 1, 1],
            "legal_ball_event": [1, 1, 1],
        }
    )

    scored = compute_pressure_index(deliveries)

    assert scored.get_column("pressure_index").to_list()[:2] == [70.0, 90.0]
    assert scored.get_column("pressure_index").to_list()[2] == pytest.approx(95.3541666667)
    assert scored.get_column("is_high_pressure").to_list() == [True, True, True]
    assert scored.get_column("pressure_regime").to_list() == [
        "high_pressure",
        "critical_leverage",
        "critical_leverage",
    ]
