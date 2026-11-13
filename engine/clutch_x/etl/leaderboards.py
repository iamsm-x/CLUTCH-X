"""Build deterministic, reliability-adjusted Top-10 leaderboards."""

import polars as pl

TOP_K = 10


def _percentile(
    frame: pl.DataFrame,
    metric: str,
    output: str,
    *,
    higher_is_better: bool,
) -> pl.DataFrame:
    rank = pl.col(metric).rank(method="average", descending=higher_is_better)
    percentile = pl.when(pl.len() > 1).then(
        (pl.len() - rank) * 100 / (pl.len() - 1)
    ).otherwise(100.0)
    return frame.with_columns(percentile.fill_null(50.0).alias(output))


def _top_ten(
    frame: pl.DataFrame,
    *,
    percentiles: tuple[tuple[str, str, bool], ...],
    baseline_expression: pl.Expr,
    rating_expression: pl.Expr,
    volume_column: str,
    top_k: int | None,
) -> pl.DataFrame:
    if frame.get_column("player_id").n_unique() != frame.height:
        raise ValueError("Leaderboard candidates contain duplicate player IDs")
    if top_k is not None and frame.height < top_k:
        raise ValueError(
            f"Need at least {top_k} eligible players for a Top-{top_k} leaderboard; "
            f"received {frame.height}"
        )

    scored = frame
    for metric, output, higher_is_better in percentiles:
        scored = _percentile(
            scored,
            metric,
            output,
            higher_is_better=higher_is_better,
        )
    scored = scored.with_columns(
        baseline_expression.alias("baseline_rating"),
    ).with_columns(
        rating_expression.alias("pressure_rating"),
    ).with_columns(
        (pl.col("pressure_rating") - pl.col("baseline_rating")).alias(
            "net_clutch_delta"
        ),
    ).with_columns(
        (
            0.55 * pl.col("pressure_rating")
            + 0.25 * ((pl.col("net_clutch_delta") + 100) / 2).clip(0, 100)
            + 0.20 * (pl.col("positive_impact_rate") * 100).clip(0, 100)
        )
        .clip(0, 100)
        .alias("clutch_x_score")
    )
    ranked = scored.sort(
        [
            "clutch_x_score",
            "pressure_rating",
            "net_clutch_delta",
            volume_column,
            "player_id",
        ],
        descending=[True, True, True, True, False],
    )
    if top_k is not None:
        ranked = ranked.head(top_k)
    ranked = ranked.with_row_index("rank", offset=1)
    if top_k is not None and ranked.get_column("player_id").n_unique() != top_k:
        raise ValueError("Top-10 output is not unique by player ID")
    return ranked


def build_batting_top10(
    eligible: pl.DataFrame,
    *,
    top_k: int | None = TOP_K,
) -> pl.DataFrame:
    """Create the batting leaderboard with explicit baseline/pressure ratings."""
    percentiles = (
        ("normal_strike_rate", "baseline_sr_pct", True),
        ("normal_boundary_rate", "baseline_boundary_pct", True),
        ("normal_dot_rate", "baseline_dot_avoidance_pct", False),
        ("volatility_adjusted_prae", "pressure_prae_pct", True),
        ("shrunk_strike_rate_delta", "pressure_sr_delta_pct", True),
        ("shrunk_boundary_rate_delta", "pressure_boundary_delta_pct", True),
        ("shrunk_dot_rate_improvement", "pressure_dot_improvement_pct", True),
        ("shrunk_wicket_preservation_delta", "pressure_wicket_preservation_pct", True),
    )
    baseline_rating = (
        0.60 * pl.col("baseline_sr_pct")
        + 0.20 * pl.col("baseline_boundary_pct")
        + 0.20 * pl.col("baseline_dot_avoidance_pct")
    )
    pressure_rating = (
        0.40 * pl.col("pressure_prae_pct")
        + 0.25 * pl.col("pressure_sr_delta_pct")
        + 0.10 * pl.col("pressure_boundary_delta_pct")
        + 0.10 * pl.col("pressure_dot_improvement_pct")
        + 0.10 * pl.col("pressure_wicket_preservation_pct")
        + 0.05 * (pl.col("positive_impact_rate") * 100)
    )
    return _top_ten(
        eligible,
        percentiles=percentiles,
        baseline_expression=baseline_rating,
        rating_expression=pressure_rating,
        volume_column="high_pressure_balls_faced",
        top_k=top_k,
    )


def build_bowling_top10(
    eligible: pl.DataFrame,
    *,
    top_k: int | None = TOP_K,
) -> pl.DataFrame:
    """Create the bowling leaderboard with explicit baseline/pressure ratings."""
    percentiles = (
        ("normal_economy", "baseline_economy_pct", False),
        ("normal_dot_rate", "baseline_dot_pct", True),
        ("normal_wickets_per_24_balls", "baseline_wickets_pct", True),
        ("volatility_adjusted_prsae", "pressure_prsae_pct", True),
        ("shrunk_economy_delta", "pressure_economy_delta_pct", True),
        ("shrunk_dot_rate_improvement", "pressure_dot_improvement_pct", True),
        (
            "shrunk_clutch_wicket_impact_per_24_balls",
            "pressure_wicket_impact_pct",
            True,
        ),
    )
    baseline_rating = (
        0.60 * pl.col("baseline_economy_pct")
        + 0.20 * pl.col("baseline_dot_pct")
        + 0.20 * pl.col("baseline_wickets_pct")
    )
    pressure_rating = (
        0.40 * pl.col("pressure_prsae_pct")
        + 0.25 * pl.col("pressure_economy_delta_pct")
        + 0.10 * pl.col("pressure_dot_improvement_pct")
        + 0.20 * pl.col("pressure_wicket_impact_pct")
        + 0.05 * (pl.col("positive_impact_rate") * 100)
    )
    return _top_ten(
        eligible,
        percentiles=percentiles,
        baseline_expression=baseline_rating,
        rating_expression=pressure_rating,
        volume_column="high_pressure_legal_balls",
        top_k=top_k,
    )


def build_batting_rankings(eligible: pl.DataFrame) -> pl.DataFrame:
    """Rank the full eligible batting cohort using the Top-10 score definition."""
    return build_batting_top10(eligible, top_k=None)


def build_bowling_rankings(eligible: pl.DataFrame) -> pl.DataFrame:
    """Rank the full eligible bowling cohort using the Top-10 score definition."""
    return build_bowling_top10(eligible, top_k=None)
