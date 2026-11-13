import polars as pl

from clutch_x.etl.ranking_audit import (
    _top10_exposure,
    split_half_rank_stability,
    validate_top10,
)


def test_split_half_alternates_each_players_matches_and_correlates_ranks() -> None:
    match_impacts = pl.DataFrame(
        {
            "player_id": [1] * 4 + [2] * 4 + [3] * 4,
            "match_id": list(range(1, 5)) * 3,
            "match_net_impact": [10, 10, 9, 9, 8, 8, 7, 7, 6, 6, 5, 5],
            "high_pressure_balls_faced": [100] * 12,
        }
    )
    dates = pl.DataFrame(
        {
            "match_id": list(range(1, 5)),
            "match_date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        }
    )

    rho, players = split_half_rank_stability(
        match_impacts,
        dates,
        impact_column="match_net_impact",
        balls_column="high_pressure_balls_faced",
        scale=100,
    )

    assert rho == 1.0
    assert players == 3


def test_top10_validator_rejects_duplicate_player_ids() -> None:
    leaderboard = pl.DataFrame(
        {
            "rank": list(range(1, 11)),
            "player_id": [1] * 10,
            "clutch_x_score": [100 - rank for rank in range(10)],
        }
    )

    try:
        validate_top10(leaderboard)
    except ValueError as exc:
        assert "duplicate player IDs" in str(exc)
    else:
        raise AssertionError("Expected duplicate player IDs to be rejected")


def test_top10_exposure_breaks_volume_ties_by_player_id() -> None:
    deliveries = pl.DataFrame(
        {
            "match_format": ["T20"] * 4,
            "competition_name": ["Indian Premier League (IPL)"] * 4,
            "is_high_pressure": [True] * 4,
            "bowler_id": [3, 1, 2, 1],
            "innings": [1] * 4,
            "legal_ball_event": [1] * 4,
        }
    )
    leaderboard = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_name": ["One", "Two", "Three"],
        }
    )

    exposure, _ = _top10_exposure(
        deliveries,
        leaderboard,
        player_column="bowler_id",
        volume_expression=pl.col("legal_ball_event"),
    )

    assert exposure.select("player_id", "high_pressure_volume").rows() == [
        (1, 2),
        (2, 1),
        (3, 1),
    ]
