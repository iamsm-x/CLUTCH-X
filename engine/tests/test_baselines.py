import polars as pl
import pytest

from clutch_x.etl.baselines import compute_personal_baselines


def test_personal_baselines_use_only_normal_pressure_and_role_specific_runs() -> None:
    deliveries = pl.DataFrame(
        {
            "is_high_pressure": [False, False, False, True],
            "striker_id": [1, 1, 1, 1],
            "striker_name": ["Batter"] * 4,
            "bowler_id": [2, 2, 2, 2],
            "bowler_name": ["Bowler"] * 4,
            "match_id": [10, 10, 11, 12],
            "innings": [1, 1, 2, 1],
            "extras_type": ["None", "byes", "wide", "None"],
            "runs": [4, 0, 0, 6],
            "is_four": [True, False, False, False],
            "is_six": [False, False, False, True],
            "delivery_total_runs": [4, 1, 1, 6],
            "legal_ball_event": [1, 1, 0, 1],
            "is_wicket": [False, True, False, False],
            "dismissed_player_id": [None, 1, None, None],
            "dismissal_type": [None, "Caught", None, None],
            "extras1_runs": [0, 1, 1, 0],
            "extras_2_runs": [0, 0, 0, 0],
        }
    )

    batting, bowling = compute_personal_baselines(deliveries)
    batter = batting.row(0, named=True)
    bowler = bowling.row(0, named=True)

    assert batter["normal_balls_faced"] == 2
    assert batter["normal_strike_rate"] == pytest.approx(200)
    assert batter["normal_boundary_rate"] == pytest.approx(0.5)
    assert batter["normal_dismissals"] == 1
    assert batter["normal_matches"] == 2
    assert bowler["normal_legal_balls"] == 2
    assert bowler["normal_runs_conceded"] == 5
    assert bowler["normal_economy"] == pytest.approx(15)
    assert bowler["normal_bowler_wickets"] == 1
