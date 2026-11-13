"""Parameterized DuckDB queries and filtered analytics assembly."""

from dataclasses import dataclass

import duckdb
import polars as pl

from clutch_x.api.schemas import AnalyticsFilters
from clutch_x.etl.batting_metrics import compute_batting_pressure_metrics
from clutch_x.etl.baselines import compute_personal_baselines
from clutch_x.etl.bowling_metrics import compute_bowling_pressure_metrics
from clutch_x.etl.leaderboards import (
    TOP_K,
    build_batting_rankings,
    build_bowling_rankings,
)
from clutch_x.etl.reliability import (
    apply_batting_reliability,
    apply_bowling_reliability,
)


@dataclass(frozen=True)
class _ScoredCohorts:
    deliveries: pl.DataFrame
    batting_rankings: pl.DataFrame
    bowling_rankings: pl.DataFrame
    batting_match_impacts: pl.DataFrame
    bowling_match_impacts: pl.DataFrame


def _execute_frame(
    connection: duckdb.DuckDBPyConnection,
    query: str,
    parameters: list[object] | None = None,
) -> pl.DataFrame:
    cursor = connection.execute(query, parameters or [])
    duckdb_types = {
        "BIGINT": pl.Int64,
        "HUGEINT": pl.Int64,
        "UINTEGER": pl.UInt32,
        "UBIGINT": pl.UInt64,
        "INTEGER": pl.Int32,
        "BOOLEAN": pl.Boolean,
        "DOUBLE": pl.Float64,
        "FLOAT": pl.Float32,
        "VARCHAR": pl.String,
    }
    schema = {}
    for column, duckdb_type, *_ in cursor.description:
        type_name = str(duckdb_type).upper()
        if type_name not in duckdb_types:
            raise TypeError(f"Unsupported DuckDB result type {type_name} for {column}")
        schema[column] = duckdb_types[type_name]
    return pl.DataFrame(cursor.fetchall(), schema=schema, orient="row")


def _where_clause(
    filters: AnalyticsFilters,
    *,
    include_over: bool,
) -> tuple[str, list[object]]:
    conditions = []
    parameters: list[object] = []
    if filters.competition == "IPL":
        conditions.append("competition_name ILIKE ?")
        parameters.append("%IPL%")
    elif filters.competition == "T20I":
        conditions.append("match_format = ?")
        parameters.append("T20I")
    if filters.innings is not None:
        conditions.append("innings = ?")
        parameters.append(filters.innings)
    if filters.match_stage == "LEAGUE":
        conditions.append("COALESCE(knock_out, FALSE) = FALSE")
    elif filters.match_stage == "KNOCKOUTS_PLAYOFFS":
        conditions.append("COALESCE(knock_out, FALSE) = TRUE")
    if include_over and filters.over is not None:
        conditions.append("overid = ?")
        parameters.append(filters.over)
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, parameters


def _filtered_deliveries(
    connection: duckdb.DuckDBPyConnection,
    filters: AnalyticsFilters,
    *,
    include_over: bool = True,
) -> pl.DataFrame:
    where, parameters = _where_clause(filters, include_over=include_over)
    return _execute_frame(
        connection, "SELECT * FROM normalized_deliveries" + where, parameters
    )


def query_filter_options(
    connection: duckdb.DuckDBPyConnection,
) -> dict[str, list[object]]:
    """Return distinct competition seasons and the supported filter choices."""
    seasons = connection.execute(
        "SELECT DISTINCT season FROM normalized_deliveries "
        "WHERE season IS NOT NULL ORDER BY season"
    ).fetchall()
    return {
        "competitions": ["ALL", "IPL", "T20I"],
        "seasons": [str(row[0]) for row in seasons],
        "match_stages": ["ALL", "LEAGUE", "KNOCKOUTS_PLAYOFFS"],
        "innings": [1, 2],
        "minimum_high_pressure_balls": [100, 150, 200, 250, 300],
    }


def _score_filtered_cohorts(
    connection: duckdb.DuckDBPyConnection,
    filters: AnalyticsFilters,
) -> _ScoredCohorts:
    deliveries = _filtered_deliveries(connection, filters)
    if deliveries.is_empty():
        raise ValueError("No deliveries match the requested analytics filters")

    batting_baselines, bowling_baselines = compute_personal_baselines(deliveries)
    batting_metrics, batting_impacts = compute_batting_pressure_metrics(
        deliveries, batting_baselines
    )
    bowling_metrics, bowling_impacts = compute_bowling_pressure_metrics(
        deliveries, bowling_baselines
    )
    batting_eligible = apply_batting_reliability(batting_metrics, batting_impacts)
    bowling_eligible = apply_bowling_reliability(bowling_metrics, bowling_impacts)
    batting_eligible = batting_eligible.filter(
        pl.col("high_pressure_balls_faced") >= filters.min_high_pressure_balls
    )
    bowling_eligible = bowling_eligible.filter(
        pl.col("high_pressure_legal_balls") >= filters.min_high_pressure_balls
    )
    return _ScoredCohorts(
        deliveries=deliveries,
        batting_rankings=build_batting_rankings(batting_eligible),
        bowling_rankings=build_bowling_rankings(bowling_eligible),
        batting_match_impacts=batting_impacts,
        bowling_match_impacts=bowling_impacts,
    )


def query_leaderboard(
    connection: duckdb.DuckDBPyConnection,
    discipline: str,
    filters: AnalyticsFilters,
) -> pl.DataFrame:
    """Recompute a filtered Top-10 using the same baseline and rating pipeline."""
    if discipline not in {"batting", "bowling"}:
        raise ValueError(f"Unsupported leaderboard discipline: {discipline}")
    scored = _score_filtered_cohorts(connection, filters)
    rankings = (
        scored.batting_rankings
        if discipline == "batting"
        else scored.bowling_rankings
    )
    if rankings.height < TOP_K:
        raise ValueError(
            f"Only {rankings.height} eligible {discipline} players match these filters; "
            f"at least {TOP_K} are required"
        )
    return rankings.head(TOP_K)


def query_pressure_timeline(
    connection: duckdb.DuckDBPyConnection,
    innings: int,
    filters: AnalyticsFilters,
) -> pl.DataFrame:
    """Aggregate average PI, high-pressure deliveries, and wickets by over."""
    if innings not in {1, 2}:
        raise ValueError("Innings must be 1 or 2")
    if filters.innings is not None and filters.innings != innings:
        raise ValueError("Timeline innings conflicts with the innings filter")
    timeline_filters = filters.model_copy(update={"innings": innings})
    where, parameters = _where_clause(timeline_filters, include_over=False)
    return _execute_frame(
        connection,
        "SELECT overid AS over, AVG(pressure_index) AS average_pressure_index, "
        "COUNT(*) FILTER (WHERE is_high_pressure) AS high_pressure_deliveries, "
        "SUM(CAST(is_wicket AS INTEGER)) AS wickets "
        "FROM normalized_deliveries"
        + where
        + " GROUP BY overid ORDER BY overid",
        parameters,
    )


def query_quadrant_scatter(
    connection: duckdb.DuckDBPyConnection,
    discipline: str,
    filters: AnalyticsFilters,
) -> tuple[float, float, pl.DataFrame]:
    """Return cohort medians and all ranked players for the quadrant chart."""
    if discipline not in {"batting", "bowling"}:
        raise ValueError(f"Unsupported scatter discipline: {discipline}")
    scored = _score_filtered_cohorts(connection, filters)
    rankings = (
        scored.batting_rankings
        if discipline == "batting"
        else scored.bowling_rankings
    )
    if rankings.is_empty():
        raise ValueError(f"No eligible {discipline} players match these filters")
    return (
        float(rankings.get_column("baseline_rating").median()),
        float(rankings.get_column("pressure_rating").median()),
        rankings.select(
            "rank",
            "player_id",
            "player_name",
            "baseline_rating",
            "pressure_rating",
            "net_clutch_delta",
        ),
    )


def query_player_comparison(
    connection: duckdb.DuckDBPyConnection,
    discipline: str,
    player_ids: list[int],
    filters: AnalyticsFilters,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return selected eligible player rankings and their match-impact rows."""
    if discipline not in {"batting", "bowling"}:
        raise ValueError(f"Unsupported comparison discipline: {discipline}")
    if not 1 <= len(player_ids) <= 3 or len(set(player_ids)) != len(player_ids):
        raise ValueError("Select one to three unique player IDs")
    scored = _score_filtered_cohorts(connection, filters)
    rankings = (
        scored.batting_rankings
        if discipline == "batting"
        else scored.bowling_rankings
    )
    impacts = (
        scored.batting_match_impacts
        if discipline == "batting"
        else scored.bowling_match_impacts
    )
    selected = rankings.filter(pl.col("player_id").is_in(player_ids))
    missing_ids = sorted(set(player_ids) - set(selected.get_column("player_id").to_list()))
    if missing_ids:
        raise ValueError(
            f"Player IDs are not eligible under these filters: {missing_ids}"
        )
    match_dates = scored.deliveries.select("match_id", "match_date").unique()
    audit = (
        impacts.filter(pl.col("player_id").is_in(player_ids))
        .join(match_dates, on="match_id", how="left", validate="m:1")
        .sort(["player_id", "match_date", "match_id"])
    )
    return selected, audit


def query_match_audit(
    connection: duckdb.DuckDBPyConnection,
    discipline: str,
    player_id: int,
    filters: AnalyticsFilters,
) -> pl.DataFrame:
    """Return one eligible player's chronological match impact audit."""
    _, audit = query_player_comparison(connection, discipline, [player_id], filters)
    return audit
