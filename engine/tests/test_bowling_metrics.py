import polars as pl
import pytest

from clutch_x.etl.bowling_metrics import compute_bowling_pressure_metrics


def test_bowling_metrics_exclude_byes_but_charge_wides() -> None:
    deliveries = pl.DataFrame(
        {
            "is_high_pressure": [True, True, True],
            "bowler_id": [2] * 3,
            "bowler_name": ["Bowler"] * 3,
            "match_id": [10, 10, 11],
            "innings": [1, 1, 2],
            "delivery_total_runs": [4, 1, 1],
            "expected_bowler_runs": [2.0, 1.0, 1.0],
            "legal_ball_event": [1, 1, 0],
            "is_wicket": [True, False, False],
            "dismissal_type": ["Caught", None, None],
            "batting_order": [4, None, None],
            "extras_type": ["None", "byes", "wide"],
            "extras1_runs": [0, 1, 1],
            "extras_2_runs": [0, 0, 0],
        }
    )
    baselines = pl.DataFrame(
        {
            "player_id": [2],
            "normal_economy": [12.0],
            "normal_dot_rate": [0.3],
            "normal_wickets_per_24_balls": [1.0],
        }
    )

    players, matches = compute_bowling_pressure_metrics(deliveries, baselines)
    bowler = players.row(0, named=True)

    assert bowler["high_pressure_legal_balls"] == 2
    assert bowler["high_pressure_runs_conceded"] == 5
    assert bowler["high_pressure_economy"] == pytest.approx(15)
    assert bowler["economy_delta"] == pytest.approx(-3)
    assert bowler["pressure_runs_saved_above_expected"] == pytest.approx(-1)
    assert bowler["prsae_per_over"] == pytest.approx(-3)
    assert bowler["high_pressure_wickets"] == 1
    assert bowler["clutch_wicket_impact_per_24_balls"] == pytest.approx(18)
    assert matches.get_column("match_runs_saved").to_list() == [-1.0, 0.0]
