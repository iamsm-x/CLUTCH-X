"""Strict Pydantic v2 contracts for the CLUTCH-X analytics API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CompetitionFilter = Literal["ALL", "IPL", "T20I"]
InningsFilter = Literal[1, 2]
MatchStageFilter = Literal["ALL", "LEAGUE", "KNOCKOUTS_PLAYOFFS"]
Discipline = Literal["batting", "bowling"]

PlayerId = Annotated[int, Field(gt=0)]
PlayerName = Annotated[str, Field(min_length=1)]
Rank = Annotated[int, Field(ge=1, le=10)]
PressureIndex = Annotated[float, Field(ge=0, le=100)]
Rating = Annotated[float, Field(ge=0, le=100)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AnalyticsFilters(StrictModel):
    competition: CompetitionFilter = "ALL"
    innings: InningsFilter | None = None
    match_stage: MatchStageFilter = "ALL"
    min_high_pressure_balls: int = Field(default=150, ge=100, le=300)
    over: int | None = Field(default=None, ge=1, le=20)


class FilterOptionsResponse(StrictModel):
    competitions: list[CompetitionFilter]
    seasons: list[str]
    match_stages: list[MatchStageFilter]
    innings: list[InningsFilter]
    minimum_high_pressure_balls: list[int]


class OverviewResponse(StrictModel):
    product_name: Literal["CLUTCH-X"]
    competitions: list[Literal["IPL", "T20I"]]
    first_season: str
    latest_season: str
    delivery_count: int = Field(ge=0)
    match_count: int = Field(ge=0)
    eligible_batters: int = Field(ge=0)
    eligible_bowlers: int = Field(ge=0)
    high_pressure_cutoff: PressureIndex
    store_schema_version: str
    split_half_stability_target: float = Field(ge=0, le=1)
    batting_split_half_rho: float = Field(ge=-1, le=1)
    bowling_split_half_rho: float = Field(ge=-1, le=1)
    rankings_meet_stability_target: bool


class BattingLeaderboardEntry(StrictModel):
    rank: Rank
    player_id: PlayerId
    player_name: PlayerName
    high_pressure_balls_faced: int = Field(ge=0)
    high_pressure_matches: int = Field(ge=0)
    normal_strike_rate: float
    high_pressure_strike_rate: float
    strike_rate_delta: float
    prae_per_100: float
    positive_impact_rate: float = Field(ge=0, le=1)
    baseline_rating: Rating
    pressure_rating: Rating
    net_clutch_delta: float
    clutch_x_score: Rating


class BowlingLeaderboardEntry(StrictModel):
    rank: Rank
    player_id: PlayerId
    player_name: PlayerName
    high_pressure_legal_balls: int = Field(ge=0)
    high_pressure_matches: int = Field(ge=0)
    normal_economy: float
    high_pressure_economy: float
    economy_delta: float
    prsae_per_over: float
    high_pressure_dot_rate: float = Field(ge=0, le=1)
    high_pressure_wickets: int = Field(ge=0)
    positive_impact_rate: float = Field(ge=0, le=1)
    baseline_rating: Rating
    pressure_rating: Rating
    net_clutch_delta: float
    clutch_x_score: Rating


class Top10Response(StrictModel):
    discipline: Discipline
    filters: AnalyticsFilters
    entries: list[BattingLeaderboardEntry | BowlingLeaderboardEntry] = Field(
        min_length=10,
        max_length=10,
    )

    @model_validator(mode="after")
    def validate_ranked_entries(self) -> "Top10Response":
        ranks = [entry.rank for entry in self.entries]
        player_ids = [entry.player_id for entry in self.entries]
        if ranks != list(range(1, 11)):
            raise ValueError("Top-10 ranks must be strictly ordered from 1 through 10")
        if len(set(player_ids)) != 10:
            raise ValueError("Top-10 player IDs must be unique")
        expected_entry = (
            BattingLeaderboardEntry
            if self.discipline == "batting"
            else BowlingLeaderboardEntry
        )
        if any(not isinstance(entry, expected_entry) for entry in self.entries):
            raise ValueError(f"{self.discipline} response contains the wrong entry type")
        return self


class MatchAuditRecord(StrictModel):
    match_id: int = Field(gt=0)
    match_date: str
    high_pressure_volume: int = Field(ge=0)
    impact: float
    impact_rate: float | None
    is_positive_impact: bool


class PlayerComparison(StrictModel):
    player_id: PlayerId
    player_name: PlayerName
    rank: Rank | None
    baseline_rating: Rating
    pressure_rating: Rating
    net_clutch_delta: float
    high_pressure_volume: int = Field(ge=0)
    high_pressure_matches: int = Field(ge=0)
    primary_metric_name: str
    normal_primary_metric: float
    pressure_primary_metric: float
    primary_metric_delta: float
    match_audit: list[MatchAuditRecord]


class PlayerComparisonResponse(StrictModel):
    discipline: Discipline
    filters: AnalyticsFilters
    players: list[PlayerComparison] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_unique_players(self) -> "PlayerComparisonResponse":
        player_ids = [player.player_id for player in self.players]
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("Comparison player IDs must be unique")
        return self


class OverTimelinePoint(StrictModel):
    over: int = Field(ge=1, le=20)
    average_pressure_index: PressureIndex
    high_pressure_deliveries: int = Field(ge=0)
    wickets: int = Field(ge=0)


class PressureTimelineResponse(StrictModel):
    innings: InningsFilter
    filters: AnalyticsFilters
    overs: list[OverTimelinePoint] = Field(max_length=20)

    @model_validator(mode="after")
    def validate_over_order(self) -> "PressureTimelineResponse":
        over_numbers = [point.over for point in self.overs]
        if over_numbers != sorted(set(over_numbers)):
            raise ValueError("Timeline overs must be unique and in ascending order")
        return self


class ScatterPoint(StrictModel):
    player_id: PlayerId
    player_name: PlayerName
    baseline_rating: Rating
    pressure_rating: Rating
    net_clutch_delta: float
    rank: Rank | None


class QuadrantScatterResponse(StrictModel):
    discipline: Discipline
    filters: AnalyticsFilters
    baseline_median: Rating
    pressure_median: Rating
    points: list[ScatterPoint]

    @model_validator(mode="after")
    def validate_unique_players(self) -> "QuadrantScatterResponse":
        player_ids = [point.player_id for point in self.points]
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("Scatter player IDs must be unique")
        return self
