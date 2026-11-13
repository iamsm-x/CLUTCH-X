import pytest
from pydantic import ValidationError

from clutch_x.api.schemas import (
    AnalyticsFilters,
    BattingLeaderboardEntry,
    PlayerComparison,
    PlayerComparisonResponse,
    PressureTimelineResponse,
    Top10Response,
)


def _batting_entry(rank: int, player_id: int) -> dict[str, object]:
    return {
        "rank": rank,
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "high_pressure_balls_faced": 200,
        "high_pressure_matches": 12,
        "normal_strike_rate": 130.0,
        "high_pressure_strike_rate": 145.0,
        "strike_rate_delta": 15.0,
        "prae_per_100": 7.2,
        "positive_impact_rate": 0.6,
        "baseline_rating": 70.0,
        "pressure_rating": 82.0,
        "net_clutch_delta": 12.0,
        "clutch_x_score": 80.0,
    }


def test_filters_reject_out_of_range_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AnalyticsFilters(min_high_pressure_balls=301)
    with pytest.raises(ValidationError):
        AnalyticsFilters(competition="ALL", unrecognized=True)


def test_top10_response_requires_ordered_unique_ids_and_matching_discipline() -> None:
    entries = [
        BattingLeaderboardEntry(**_batting_entry(rank, rank))
        for rank in range(1, 11)
    ]
    response = Top10Response(
        discipline="batting",
        filters=AnalyticsFilters(),
        entries=entries,
    )
    assert len(response.entries) == 10

    duplicated = entries.copy()
    duplicated[-1] = BattingLeaderboardEntry(**_batting_entry(10, 1))
    with pytest.raises(ValidationError, match="player IDs must be unique"):
        Top10Response(
            discipline="batting",
            filters=AnalyticsFilters(),
            entries=duplicated,
        )


def test_comparison_and_timeline_enforce_cardinality_and_order() -> None:
    player = PlayerComparison(
        player_id=1,
        player_name="Player 1",
        rank=1,
        baseline_rating=70,
        pressure_rating=80,
        net_clutch_delta=10,
        high_pressure_volume=200,
        high_pressure_matches=12,
        primary_metric_name="strike_rate",
        normal_primary_metric=130,
        pressure_primary_metric=145,
        primary_metric_delta=15,
        match_audit=[],
    )
    with pytest.raises(ValidationError, match="player IDs must be unique"):
        PlayerComparisonResponse(
            discipline="batting",
            filters=AnalyticsFilters(),
            players=[player, player],
        )
    with pytest.raises(ValidationError, match="ascending order"):
        PressureTimelineResponse(
            innings=1,
            filters=AnalyticsFilters(innings=1),
            overs=[
                {
                    "over": 2,
                    "average_pressure_index": 61.0,
                    "high_pressure_deliveries": 5,
                    "wickets": 1,
                },
                {
                    "over": 1,
                    "average_pressure_index": 58.0,
                    "high_pressure_deliveries": 3,
                    "wickets": 0,
                },
            ],
        )
