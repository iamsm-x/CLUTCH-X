import polars as pl

from clutch_x.etl.leaderboards import build_batting_top10, build_bowling_top10


def test_leaderboards_are_ordered_unique_and_have_a_stable_rank_tiebreak() -> None:
    player_ids = list(range(1, 11))
    ascending = [float(value) for value in player_ids]
    consistency = [value / 10 for value in player_ids]
    batting = pl.DataFrame(
        {
            "player_id": player_ids,
            "player_name": [f"Batter {value}" for value in player_ids],
            "normal_strike_rate": ascending,
            "normal_boundary_rate": ascending,
            "normal_dot_rate": [1 - value / 20 for value in player_ids],
            "volatility_adjusted_prae": ascending,
            "shrunk_strike_rate_delta": ascending,
            "shrunk_boundary_rate_delta": ascending,
            "shrunk_dot_rate_improvement": ascending,
            "shrunk_wicket_preservation_delta": ascending,
            "positive_impact_rate": consistency,
            "high_pressure_balls_faced": [150] * 10,
        }
    )
    bowling = pl.DataFrame(
        {
            "player_id": player_ids,
            "player_name": [f"Bowler {value}" for value in player_ids],
            "normal_economy": [11 - value for value in player_ids],
            "normal_dot_rate": ascending,
            "normal_wickets_per_24_balls": ascending,
            "volatility_adjusted_prsae": ascending,
            "shrunk_economy_delta": ascending,
            "shrunk_dot_rate_improvement": ascending,
            "shrunk_clutch_wicket_impact_per_24_balls": ascending,
            "positive_impact_rate": consistency,
            "high_pressure_legal_balls": [150] * 10,
        }
    )

    batting_top10 = build_batting_top10(batting)
    bowling_top10 = build_bowling_top10(bowling)

    assert batting_top10.get_column("rank").to_list() == list(range(1, 11))
    assert bowling_top10.get_column("rank").to_list() == list(range(1, 11))
    assert batting_top10.get_column("player_id").to_list() == list(range(10, 0, -1))
    assert bowling_top10.get_column("player_id").to_list() == list(range(10, 0, -1))
    assert batting_top10.get_column("player_id").n_unique() == 10
    assert bowling_top10.get_column("player_id").n_unique() == 10
