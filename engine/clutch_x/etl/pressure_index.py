"""Compute CLUTCH-X's deterministic delivery-level Pressure Index.

The initial transparent specification weights nonlinear chase-rate tension at
75% and resource scarcity at 25%. First-innings pressure is the stronger of a
collapse trigger and a linear death-over urgency score. Knockout matches receive
a 1.15 multiplier, and the final score is clamped to [0, 100].
"""

import polars as pl

KNOCKOUT_MULTIPLIER = 1.15
CHASE_TENSION_WEIGHT = 0.75
RESOURCE_SCARCITY_WEIGHT = 0.25
HIGH_PRESSURE_CUTOFF = 60.0
NORMAL_T20_LEGAL_BALLS = 120


def _par_run_rates(deliveries: pl.DataFrame) -> pl.DataFrame:
    first_innings_rates = (
        deliveries.filter(pl.col("innings") == 1)
        .group_by(["match_id", "match_format", "season"])
        .agg(
            pl.col("delivery_total_runs").sum().alias("match_runs"),
            pl.col("legal_ball_event").sum().alias("match_legal_balls"),
        )
        .filter(pl.col("match_legal_balls") > 0)
        .with_columns(
            (pl.col("match_runs") * 6 / pl.col("match_legal_balls")).alias("match_par_rate")
        )
    )
    return first_innings_rates.group_by(["match_format", "season"]).agg(
        pl.col("match_par_rate").mean().alias("par_run_rate")
    )


def compute_pressure_index(deliveries: pl.DataFrame) -> pl.DataFrame:
    """Return each input delivery with auditable PI component columns."""
    required = {
        "match_id", "innings", "match_format", "season", "overid", "pre_delivery_wickets",
        "balls_remaining", "scheduled_legal_balls", "runs_required", "knock_out",
        "delivery_total_runs", "legal_ball_event",
    }
    missing = required - set(deliveries.columns)
    if missing:
        raise ValueError(f"Pressure Index input missing columns: {', '.join(sorted(missing))}")

    scored = deliveries.join(
        _par_run_rates(deliveries),
        on=["match_format", "season"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.when((pl.col("innings") == 2) & (pl.col("balls_remaining") > 0))
        .then(pl.col("runs_required").clip(lower_bound=0) * 6 / pl.col("balls_remaining"))
        .otherwise(0.0)
        .alias("required_run_rate"),
        (
            pl.col("pre_delivery_wickets").clip(0, 9) / 9
            * (
                1
                - pl.col("balls_remaining")
                / pl.col("scheduled_legal_balls").clip(lower_bound=1)
            ).clip(0, 1)
        ).alias("resource_scarcity"),
    ).with_columns(
        (
            pl.col("required_run_rate") / pl.col("par_run_rate").clip(lower_bound=0.1) - 1
        )
        .clip(0, 1)
        .alias("normalized_chase_tension"),
        (
            pl.when(
                (pl.col("innings") == 1)
                & (pl.col("overid") <= 8)
                & (pl.col("pre_delivery_wickets") >= 3)
            )
            .then(70 + 5 * (pl.col("pre_delivery_wickets") - 3).clip(lower_bound=0))
            .when(
                (pl.col("innings") == 1)
                & (pl.col("overid") <= 14)
                & (pl.col("pre_delivery_wickets") >= 5)
            )
            .then(75 + 4 * (pl.col("pre_delivery_wickets") - 5).clip(lower_bound=0))
            .otherwise(0)
        ).alias("collapse_pressure"),
        pl.when((pl.col("innings") == 1) & (pl.col("overid") >= 16))
        .then(30 + 15 * (pl.col("overid") - 16).clip(0, 5))
        .otherwise(0)
        .alias("death_over_pressure"),
    ).with_columns(
        (
            100 * pl.col("normalized_chase_tension").pow(2)
        ).alias("chase_tension_score"),
    ).with_columns(
        (
            pl.when(pl.col("innings") == 2)
            .then(
                CHASE_TENSION_WEIGHT * pl.col("chase_tension_score")
                + RESOURCE_SCARCITY_WEIGHT * pl.col("resource_scarcity") * 100
            )
            .otherwise(
                pl.max_horizontal("collapse_pressure", "death_over_pressure")
            )
        ).alias("unadjusted_pressure_index"),
    ).with_columns(
        (
            pl.col("unadjusted_pressure_index")
            * pl.when(pl.col("knock_out").fill_null(False))
            .then(KNOCKOUT_MULTIPLIER)
            .otherwise(1.0)
        )
        .clip(0, 100)
        .alias("pressure_index")
    ).with_columns(
        (pl.col("pressure_index") >= HIGH_PRESSURE_CUTOFF).alias("is_high_pressure"),
        pl.when(pl.col("pressure_index") >= 80)
        .then(pl.lit("critical_leverage"))
        .when(pl.col("pressure_index") >= HIGH_PRESSURE_CUTOFF)
        .then(pl.lit("high_pressure"))
        .when(pl.col("pressure_index") >= 40)
        .then(pl.lit("building"))
        .otherwise(pl.lit("routine"))
        .alias("pressure_regime"),
    )

    if scored.filter(pl.col("pressure_index").is_null()).height:
        raise ValueError("Pressure Index produced null values; inspect format-season par rates")
    return scored
