"""FastAPI application for filtered CLUTCH-X analytics."""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Callable, TypeVar

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from clutch_x.api.queries import (
    query_filter_options,
    query_leaderboard,
    query_match_audit,
    query_player_comparison,
    query_pressure_timeline,
    query_quadrant_scatter,
)
from clutch_x.api.schemas import (
    AnalyticsFilters,
    BattingLeaderboardEntry,
    BowlingLeaderboardEntry,
    CompetitionFilter,
    Discipline,
    FilterOptionsResponse,
    MatchAuditRecord,
    MatchStageFilter,
    OverviewResponse,
    PlayerComparison,
    PlayerComparisonResponse,
    PressureTimelineResponse,
    QuadrantScatterResponse,
    ScatterPoint,
    Top10Response,
)
from clutch_x.etl.pressure_index import HIGH_PRESSURE_CUTOFF

DATABASE_PATH = Path(
    os.environ.get("CLUTCH_X_DB", "data/processed/clutch_x.duckdb")
)

app = FastAPI(
    title="CLUTCH-X Analytics API",
    version="1.0.0",
    description="Filtered T20 pressure analytics and auditable player rankings.",
)
cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "CLUTCH_X_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

T = TypeVar("T")


def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    if not DATABASE_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Analytics database is unavailable: {DATABASE_PATH}",
        )
    try:
        connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
    except duckdb.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Analytics database could not be opened",
        ) from exc
    try:
        yield connection
    finally:
        connection.close()


def get_analytics_filters(
    competition: CompetitionFilter = "ALL",
    filter_innings: Annotated[
        int | None, Query(ge=1, le=2, alias="innings")
    ] = None,
    match_stage: MatchStageFilter = "ALL",
    min_high_pressure_balls: Annotated[int, Query(ge=100, le=300)] = 150,
    over: Annotated[int | None, Query(ge=1, le=20)] = None,
) -> AnalyticsFilters:
    return AnalyticsFilters(
        competition=competition,
        innings=filter_innings,
        match_stage=match_stage,
        min_high_pressure_balls=min_high_pressure_balls,
        over=over,
    )


def _query_or_422(function: Callable[..., T], *args: object) -> T:
    try:
        return function(*args)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _match_audit_records(
    audit_rows,
    discipline: Discipline,
) -> list[MatchAuditRecord]:
    impact_column = (
        "match_net_impact" if discipline == "batting" else "match_runs_saved"
    )
    volume_column = (
        "high_pressure_balls_faced"
        if discipline == "batting"
        else "high_pressure_legal_balls"
    )
    scale = 100 if discipline == "batting" else 6
    records = []
    for row in audit_rows.iter_rows(named=True):
        impact = float(row[impact_column])
        volume = int(row[volume_column])
        records.append(
            MatchAuditRecord(
                match_id=int(row["match_id"]),
                match_date=row["match_date"],
                high_pressure_volume=volume,
                impact=impact,
                impact_rate=impact * scale / volume if volume > 0 else None,
                is_positive_impact=impact > 0,
            )
        )
    return records


@app.get("/api/v1/overview", response_model=OverviewResponse)
def overview(
    connection: Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)],
) -> OverviewResponse:
    coverage = connection.execute(
        "SELECT COUNT(*), COUNT(DISTINCT match_id), MIN(season), MAX(season) "
        "FROM normalized_deliveries"
    ).fetchone()
    eligible_batters = connection.execute(
        "SELECT COUNT(*) FROM eligible_batters"
    ).fetchone()[0]
    eligible_bowlers = connection.execute(
        "SELECT COUNT(*) FROM eligible_bowlers"
    ).fetchone()[0]
    store_schema_version = connection.execute(
        "SELECT value FROM artifact_metadata WHERE key = 'store_schema_version'"
    ).fetchone()[0]
    stability_rows = connection.execute(
        "SELECT discipline, split_half_rho, target_rho, meets_target "
        "FROM ranking_audit_summary"
    ).fetchall()
    stability = {row[0]: row[1:] for row in stability_rows}
    return OverviewResponse(
        product_name="CLUTCH-X",
        competitions=["IPL", "T20I"],
        first_season=str(coverage[2]),
        latest_season=str(coverage[3]),
        delivery_count=coverage[0],
        match_count=coverage[1],
        eligible_batters=eligible_batters,
        eligible_bowlers=eligible_bowlers,
        high_pressure_cutoff=HIGH_PRESSURE_CUTOFF,
        store_schema_version=store_schema_version,
        split_half_stability_target=float(stability["batting"][1]),
        batting_split_half_rho=float(stability["batting"][0]),
        bowling_split_half_rho=float(stability["bowling"][0]),
        rankings_meet_stability_target=(
            stability["batting"][2] and stability["bowling"][2]
        ),
    )


@app.get("/api/v1/filters", response_model=FilterOptionsResponse)
def filters(
    connection: Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)],
) -> FilterOptionsResponse:
    return FilterOptionsResponse(**query_filter_options(connection))


@app.get("/api/v1/leaderboards/{discipline}", response_model=Top10Response)
def leaderboard(
    discipline: Discipline,
    analytics_filters: Annotated[AnalyticsFilters, Depends(get_analytics_filters)],
    connection: Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)],
) -> Top10Response:
    rankings = _query_or_422(
        query_leaderboard, connection, discipline, analytics_filters
    )
    if discipline == "batting":
        entry_type = BattingLeaderboardEntry
        columns = (
            "rank",
            "player_id",
            "player_name",
            "high_pressure_balls_faced",
            "high_pressure_matches",
            "normal_strike_rate",
            "high_pressure_strike_rate",
            "strike_rate_delta",
            "prae_per_100",
            "positive_impact_rate",
            "baseline_rating",
            "pressure_rating",
            "net_clutch_delta",
            "clutch_x_score",
        )
    else:
        entry_type = BowlingLeaderboardEntry
        columns = (
            "rank",
            "player_id",
            "player_name",
            "high_pressure_legal_balls",
            "high_pressure_matches",
            "normal_economy",
            "high_pressure_economy",
            "economy_delta",
            "prsae_per_over",
            "high_pressure_dot_rate",
            "high_pressure_wickets",
            "positive_impact_rate",
            "baseline_rating",
            "pressure_rating",
            "net_clutch_delta",
            "clutch_x_score",
        )
    entries = [
        entry_type(**row)
        for row in rankings.select(columns).to_dicts()
    ]
    return Top10Response(
        discipline=discipline,
        filters=analytics_filters,
        entries=entries,
    )


@app.get(
    "/api/v1/timeline/{innings}",
    response_model=PressureTimelineResponse,
)
def pressure_timeline(
    innings: int,
    analytics_filters: AnalyticsFilters = Depends(get_analytics_filters),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> PressureTimelineResponse:
    if innings not in {1, 2}:
        raise HTTPException(status_code=422, detail="Innings must be 1 or 2")
    timeline = _query_or_422(
        query_pressure_timeline,
        connection,
        innings,
        analytics_filters,
    )
    return PressureTimelineResponse(
        innings=innings,
        filters=analytics_filters,
        overs=timeline.to_dicts(),
    )


@app.get(
    "/api/v1/scatter/{discipline}",
    response_model=QuadrantScatterResponse,
)
def quadrant_scatter(
    discipline: Discipline,
    analytics_filters: Annotated[AnalyticsFilters, Depends(get_analytics_filters)],
    connection: Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)],
) -> QuadrantScatterResponse:
    baseline_median, pressure_median, rows = _query_or_422(
        query_quadrant_scatter,
        connection,
        discipline,
        analytics_filters,
    )
    points = []
    for row in rows.to_dicts():
        rank = row["rank"]
        points.append(
            ScatterPoint(
                **{
                    **row,
                    "rank": rank if rank <= 10 else None,
                }
            )
        )
    return QuadrantScatterResponse(
        discipline=discipline,
        filters=analytics_filters,
        baseline_median=baseline_median,
        pressure_median=pressure_median,
        points=points,
    )


@app.get(
    "/api/v1/players/compare",
    response_model=PlayerComparisonResponse,
)
def compare_players(
    discipline: Discipline,
    player_ids: Annotated[list[int], Query(min_length=1, max_length=3)],
    analytics_filters: Annotated[AnalyticsFilters, Depends(get_analytics_filters)],
    connection: Annotated[duckdb.DuckDBPyConnection, Depends(get_connection)],
) -> PlayerComparisonResponse:
    rankings, audit_rows = _query_or_422(
        query_player_comparison,
        connection,
        discipline,
        player_ids,
        analytics_filters,
    )
    if discipline == "batting":
        volume_column = "high_pressure_balls_faced"
        matches_column = "high_pressure_matches"
        normal_column = "normal_strike_rate"
        pressure_column = "high_pressure_strike_rate"
        delta_column = "strike_rate_delta"
        metric_name = "strike_rate"
    else:
        volume_column = "high_pressure_legal_balls"
        matches_column = "high_pressure_matches"
        normal_column = "normal_economy"
        pressure_column = "high_pressure_economy"
        delta_column = "economy_delta"
        metric_name = "economy"
    players = []
    for row in rankings.to_dicts():
        rank = row["rank"]
        player_id = row["player_id"]
        player_audit = audit_rows.filter(
            audit_rows.get_column("player_id") == player_id
        )
        players.append(
            PlayerComparison(
                player_id=player_id,
                player_name=row["player_name"],
                rank=rank if rank <= 10 else None,
                baseline_rating=row["baseline_rating"],
                pressure_rating=row["pressure_rating"],
                net_clutch_delta=row["net_clutch_delta"],
                high_pressure_volume=row[volume_column],
                high_pressure_matches=row[matches_column],
                primary_metric_name=metric_name,
                normal_primary_metric=row[normal_column],
                pressure_primary_metric=row[pressure_column],
                primary_metric_delta=row[delta_column],
                match_audit=_match_audit_records(player_audit, discipline),
            )
        )
    return PlayerComparisonResponse(
        discipline=discipline,
        filters=analytics_filters,
        players=players,
    )


@app.get(
    "/api/v1/players/{discipline}/{player_id}/matches",
    response_model=list[MatchAuditRecord],
)
def player_match_audit(
    discipline: Discipline,
    player_id: int,
    analytics_filters: AnalyticsFilters = Depends(get_analytics_filters),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> list[MatchAuditRecord]:
    if player_id <= 0:
        raise HTTPException(status_code=422, detail="Player ID must be positive")
    audit = _query_or_422(
        query_match_audit,
        connection,
        discipline,
        player_id,
        analytics_filters,
    )
    return _match_audit_records(audit, discipline)
