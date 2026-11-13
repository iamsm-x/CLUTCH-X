import polars as pl
import pytest

from clutch_x.etl.batting_metrics import compute_batting_pressure_metrics


def test_batting_pressure_metrics_exclude_wides_from_balls_faced() -> None:
    deliveries = pl.DataFrame(
        {
            "is_high_pressure": [True, True, True, True],
            "striker_id": [1] * 4,
            "striker_name": ["Batter"] * 4,
            "match_id": [10, 10, 11, 12],
            "innings": [1, 1, 2, 1],
            "extras_type": ["None", "None", "None", "wide"],
            "runs": [4, 0, 1, 0],
            "is_four": [True, False, False, False],
            "is_six": [False, False, False, False],
            "delivery_total_runs": [4, 0, 2, 1],
            "expected_batter_runs": [2.0, 1.0, 0.0, 0.5],
            "is_wicket": [False, False, False, False],
            "dismissed_player_id": [None] * 4,
        }
    )
    baselines = pl.DataFrame(
        {
            "player_id": [1],
            "normal_strike_rate": [100.0],
            "normal_boundary_rate": [0.2],
            "normal_dot_rate": [0.3],
            "normal_balls_per_dismissal": [20.0],
            "normal_dismissal_rate": [0.05],
        }
    )

    players, matches = compute_batting_pressure_metrics(deliveries, baselines)
    player = players.row(0, named=True)

    assert player["high_pressure_balls_faced"] == 3
    assert player["high_pressure_matches"] == 2
    assert player["high_pressure_strike_rate"] == pytest.approx(500 / 3)
    assert player["strike_rate_delta"] == pytest.approx(500 / 3 - 100)
    assert player["prae_per_100"] == pytest.approx(200 / 3)
    assert player["high_pressure_boundary_rate"] == pytest.approx(1 / 3)
    assert player["positive_impact_rate"] == 1
    assert matches.get_column("match_net_impact").to_list() == [1.0, 1.0]
