"""Compute high-pressure bowling diagnostics against personal baselines."""

import polars as pl

from clutch_x.etl.delivery_rules import (
    BOWLER_CREDITED_DISMISSALS,
    bowler_runs_conceded,
)

TOP_ORDER_WICKET_WEIGHT = 1.5


def compute_bowling_pressure_metrics(
    deliveries: pl.DataFrame,
    baselines: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return player bowling metrics and per-match impact audit rows."""
    required = {
        "is_high_pressure", "bowler_id", "bowler_name", "match_id", "innings",
        "delivery_total_runs", "expected_bowler_runs", "legal_ball_event",
        "is_wicket", "dismissal_type", "batting_order",
    }
    missing = required - set(deliveries.columns)
    if missing:
        raise ValueError(f"Bowling metrics input missing columns: {', '.join(sorted(missing))}")
    baseline_columns = {
        "player_id", "normal_economy", "normal_dot_rate", "normal_wickets_per_24_balls",
    }
    missing_baselines = baseline_columns - set(baselines.columns)
    if missing_baselines:
        raise ValueError(
            "Bowling baseline input missing columns: "
            + ", ".join(sorted(missing_baselines))
        )

    dismissal_type = pl.col("dismissal_type").fill_null("").str.to_lowercase()
    credited_wicket = (
        pl.col("is_wicket").fill_null(False)
        & dismissal_type.is_in(BOWLER_CREDITED_DISMISSALS)
    )
    pressure_balls = (
        deliveries.filter(pl.col("is_high_pressure"))
        .with_columns(
            bowler_runs_conceded().alias("_runs_conceded"),
            (pl.col("expected_bowler_runs") - bowler_runs_conceded())
            .alias("_runs_saved_above_expected"),
            credited_wicket.cast(pl.Int64).alias("_credited_wicket"),
            (
                credited_wicket
                & pl.col("batting_order").is_not_null()
                & (pl.col("batting_order") <= 6)
            )
            .cast(pl.Int64)
            .alias("_top_order_wicket"),
            (
                (pl.col("delivery_total_runs") == 0)
                & (pl.col("legal_ball_event") == 1)
            )
            .cast(pl.Int64)
            .alias("_dot_legal_ball"),
            pl.col("legal_ball_event").fill_null(0).alias("_legal_balls"),
        )
    )
    innings_impacts = (
        pressure_balls.group_by(["bowler_id", "bowler_name", "match_id", "innings"])
        .agg(
            pl.col("_runs_saved_above_expected").sum().alias("innings_runs_saved"),
            pl.col("_legal_balls").sum().alias("high_pressure_legal_balls"),
        )
        .rename({"bowler_id": "player_id", "bowler_name": "player_name"})
        .sort(["player_id", "match_id", "innings"])
    )
    match_impacts = (
        innings_impacts.group_by(["player_id", "player_name", "match_id"])
        .agg(
            pl.col("innings_runs_saved").sum().alias("match_runs_saved"),
            pl.col("high_pressure_legal_balls").sum(),
        )
        .sort(["player_id", "match_id"])
    )
    consistency = innings_impacts.group_by("player_id").agg(
        pl.len().alias("high_pressure_innings"),
        (pl.col("innings_runs_saved") > 0)
        .sum()
        .alias("positive_high_pressure_innings"),
        (pl.col("innings_runs_saved") > 0)
        .mean()
        .alias("positive_impact_rate"),
    )
    player_metrics = (
        pressure_balls.group_by("bowler_id")
        .agg(
            pl.col("bowler_name").first().alias("player_name"),
            pl.col("_runs_conceded").sum().alias("high_pressure_runs_conceded"),
            pl.col("_legal_balls").sum().alias("high_pressure_legal_balls"),
            pl.col("match_id").n_unique().alias("high_pressure_matches"),
            pl.col("_dot_legal_ball").sum().alias("high_pressure_dot_balls"),
            pl.col("_credited_wicket").sum().alias("high_pressure_wickets"),
            pl.col("_top_order_wicket")
            .sum()
            .alias("high_pressure_top_order_wickets"),
            pl.col("_runs_saved_above_expected")
            .sum()
            .alias("pressure_runs_saved_above_expected"),
        )
        .with_columns(
            pl.when(pl.col("high_pressure_legal_balls") > 0)
            .then(
                pl.col("high_pressure_runs_conceded") * 6
                / pl.col("high_pressure_legal_balls")
            )
            .otherwise(None)
            .alias("high_pressure_economy"),
            pl.when(pl.col("high_pressure_legal_balls") > 0)
            .then(
                pl.col("high_pressure_dot_balls")
                / pl.col("high_pressure_legal_balls")
            )
            .otherwise(None)
            .alias("high_pressure_dot_rate"),
            pl.when(pl.col("high_pressure_legal_balls") > 0)
            .then(
                pl.col("pressure_runs_saved_above_expected") * 6
                / pl.col("high_pressure_legal_balls")
            )
            .otherwise(None)
            .alias("prsae_per_over"),
            pl.when(pl.col("high_pressure_legal_balls") > 0)
            .then(
                pl.col("high_pressure_wickets") * 24
                / pl.col("high_pressure_legal_balls")
            )
            .otherwise(None)
            .alias("high_pressure_wickets_per_24_balls"),
            pl.when(pl.col("high_pressure_legal_balls") > 0)
            .then(
                (
                    pl.col("high_pressure_wickets")
                    + (TOP_ORDER_WICKET_WEIGHT - 1)
                    * pl.col("high_pressure_top_order_wickets")
                )
                * 24
                / pl.col("high_pressure_legal_balls")
            )
            .otherwise(None)
            .alias("clutch_wicket_impact_per_24_balls"),
        )
        .rename({"bowler_id": "player_id"})
        .join(
            baselines.select(
                "player_id",
                "normal_economy",
                "normal_dot_rate",
                "normal_wickets_per_24_balls",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(consistency, on="player_id", how="left", validate="1:1")
        .with_columns(
            (pl.col("normal_economy") - pl.col("high_pressure_economy"))
            .alias("economy_delta"),
            (pl.col("high_pressure_dot_rate") - pl.col("normal_dot_rate"))
            .alias("dot_rate_improvement"),
            (
                pl.col("high_pressure_wickets_per_24_balls")
                - pl.col("normal_wickets_per_24_balls")
            ).alias("wicket_rate_delta"),
        )
        .sort("player_id")
    )
    return player_metrics, match_impacts
