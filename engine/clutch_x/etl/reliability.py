"""Apply player eligibility, Bayesian shrinkage, and match-volatility penalties."""

import polars as pl

MIN_HIGH_PRESSURE_BALLS = 150
MIN_HIGH_PRESSURE_MATCHES = 10
SHRINKAGE_PRIOR_BALLS = 150.0
VOLATILITY_PENALTY_LAMBDA = 0.5


def _shrink_peer_metrics(
    eligible: pl.DataFrame,
    metric_names: tuple[str, ...],
) -> pl.DataFrame:
    with_peer_means = eligible.with_columns(
        pl.col(metric).mean().alias(f"peer_mean_{metric}")
        for metric in metric_names
    )
    return with_peer_means.with_columns(
        (
            pl.col(metric) * pl.col("reliability_weight")
            + pl.col(f"peer_mean_{metric}") * (1 - pl.col("reliability_weight"))
        ).alias(f"shrunk_{metric}")
        for metric in metric_names
    )


def _add_reliability(
    eligible: pl.DataFrame,
    impacts: pl.DataFrame,
    *,
    volume_column: str,
    impact_column: str,
    impact_balls_column: str,
    impact_scale: float,
    raw_metric: str,
    shrunk_metric: str,
    adjusted_metric: str,
    adjusted_peer_mean: str,
) -> pl.DataFrame:
    impact_rates = (
        impacts.filter(pl.col(impact_balls_column) > 0)
        .with_columns(
            (
                pl.col(impact_column) * impact_scale / pl.col(impact_balls_column)
            ).alias("_match_impact_rate")
        )
        .group_by("player_id")
        .agg(
            pl.col("_match_impact_rate").mean().alias("mean_match_impact"),
            pl.col("_match_impact_rate").std().fill_null(0).alias("match_impact_std"),
        )
    )
    result = eligible.join(impact_rates, on="player_id", how="left", validate="1:1")
    result = result.with_columns(
        (
            pl.col(volume_column)
            / (pl.col(volume_column) + SHRINKAGE_PRIOR_BALLS)
        ).alias("reliability_weight"),
        pl.col(raw_metric).mean().alias("_eligible_peer_mean"),
    ).with_columns(
        (
            pl.col(raw_metric) * pl.col("reliability_weight")
            + pl.col("_eligible_peer_mean") * (1 - pl.col("reliability_weight"))
        ).alias(shrunk_metric),
        (
            pl.col("mean_match_impact")
            - VOLATILITY_PENALTY_LAMBDA * pl.col("match_impact_std")
        ).alias(adjusted_metric),
        pl.col("_eligible_peer_mean").alias(adjusted_peer_mean),
    ).drop("_eligible_peer_mean")
    return result


def apply_batting_reliability(
    metrics: pl.DataFrame,
    match_impacts: pl.DataFrame,
) -> pl.DataFrame:
    """Return eligible batters with shrunk pRAE and volatility-adjusted impact."""
    eligible = metrics.filter(
        (pl.col("high_pressure_balls_faced") >= MIN_HIGH_PRESSURE_BALLS)
        & (pl.col("high_pressure_matches") >= MIN_HIGH_PRESSURE_MATCHES)
    )
    if eligible.is_empty():
        return eligible
    adjusted = _add_reliability(
        eligible,
        match_impacts,
        volume_column="high_pressure_balls_faced",
        impact_column="match_net_impact",
        impact_balls_column="high_pressure_balls_faced",
        impact_scale=100,
        raw_metric="prae_per_100",
        shrunk_metric="shrunk_prae_per_100",
        adjusted_metric="volatility_adjusted_prae",
        adjusted_peer_mean="peer_mean_prae_per_100",
    )
    return _shrink_peer_metrics(
        adjusted,
        (
            "strike_rate_delta",
            "boundary_rate_delta",
            "dot_rate_improvement",
            "wicket_preservation_delta",
        ),
    )


def apply_bowling_reliability(
    metrics: pl.DataFrame,
    match_impacts: pl.DataFrame,
) -> pl.DataFrame:
    """Return eligible bowlers with shrunk pRSAE and volatility-adjusted impact."""
    eligible = metrics.filter(
        (pl.col("high_pressure_legal_balls") >= MIN_HIGH_PRESSURE_BALLS)
        & (pl.col("high_pressure_matches") >= MIN_HIGH_PRESSURE_MATCHES)
    )
    if eligible.is_empty():
        return eligible
    adjusted = _add_reliability(
        eligible,
        match_impacts,
        volume_column="high_pressure_legal_balls",
        impact_column="match_runs_saved",
        impact_balls_column="high_pressure_legal_balls",
        impact_scale=6,
        raw_metric="prsae_per_over",
        shrunk_metric="shrunk_prsae_per_over",
        adjusted_metric="volatility_adjusted_prsae",
        adjusted_peer_mean="peer_mean_prsae_per_over",
    )
    return _shrink_peer_metrics(
        adjusted,
        (
            "economy_delta",
            "dot_rate_improvement",
            "wicket_rate_delta",
            "clutch_wicket_impact_per_24_balls",
        ),
    )
