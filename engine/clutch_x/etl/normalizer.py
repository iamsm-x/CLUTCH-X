"""Build per-delivery context-expected runs and wicket probabilities."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.delivery_rules import bowler_runs_conceded

CONTEXT_COLUMNS = ["match_format", "season", "innings", "over_phase"]
PARENT_COLUMNS = ["match_format", "innings", "over_phase"]
PRIOR_DELIVERIES = 30.0


def build_context_expectations(deliveries: pl.DataFrame) -> pl.DataFrame:
    """Attach shrunk context expectations without changing delivery grain."""
    required = set(
        CONTEXT_COLUMNS
        + [
            "delivery_total_runs", "wicket_event", "runs", "extras_type",
            "extras1_runs", "extras_2_runs",
        ]
    )
    missing = required - set(deliveries.columns)
    if missing:
        raise ValueError(f"Normalization input missing columns: {', '.join(sorted(missing))}")

    prepared = deliveries.with_columns(
        bowler_runs_conceded().alias("_bowler_runs_conceded")
    )
    buckets = prepared.group_by(CONTEXT_COLUMNS).agg(
        pl.len().alias("context_bucket_deliveries"),
        pl.col("delivery_total_runs").mean().alias("bucket_expected_runs"),
        pl.col("runs").mean().alias("bucket_expected_batter_runs"),
        pl.col("_bowler_runs_conceded").mean().alias("bucket_expected_bowler_runs"),
        pl.col("wicket_event").mean().alias("bucket_wicket_probability"),
    )
    parents = prepared.group_by(PARENT_COLUMNS).agg(
        pl.col("delivery_total_runs").mean().alias("parent_expected_runs"),
        pl.col("runs").mean().alias("parent_expected_batter_runs"),
        pl.col("_bowler_runs_conceded").mean().alias("parent_expected_bowler_runs"),
        pl.col("wicket_event").mean().alias("parent_wicket_probability"),
    )
    expected = prepared.join(
        buckets,
        on=CONTEXT_COLUMNS,
        how="left",
        validate="m:1",
    ).join(
        parents,
        on=PARENT_COLUMNS,
        how="left",
        validate="m:1",
    ).with_columns(
        (
            (
                pl.col("bucket_expected_runs") * pl.col("context_bucket_deliveries")
                + pl.col("parent_expected_runs") * PRIOR_DELIVERIES
            )
            / (pl.col("context_bucket_deliveries") + PRIOR_DELIVERIES)
        ).alias("expected_runs"),
        (
            (
                pl.col("bucket_expected_batter_runs")
                * pl.col("context_bucket_deliveries")
                + pl.col("parent_expected_batter_runs") * PRIOR_DELIVERIES
            )
            / (pl.col("context_bucket_deliveries") + PRIOR_DELIVERIES)
        ).alias("expected_batter_runs"),
        (
            (
                pl.col("bucket_expected_bowler_runs")
                * pl.col("context_bucket_deliveries")
                + pl.col("parent_expected_bowler_runs") * PRIOR_DELIVERIES
            )
            / (pl.col("context_bucket_deliveries") + PRIOR_DELIVERIES)
        ).alias("expected_bowler_runs"),
        (
            (
                pl.col("bucket_wicket_probability") * pl.col("context_bucket_deliveries")
                + pl.col("parent_wicket_probability") * PRIOR_DELIVERIES
            )
            / (pl.col("context_bucket_deliveries") + PRIOR_DELIVERIES)
        ).alias("expected_wicket_prob"),
    )
    if expected.height != deliveries.height:
        raise ValueError("Context normalization changed the delivery row count")
    if expected.select(
        pl.any_horizontal(
            pl.col("expected_runs").is_null(),
            pl.col("expected_batter_runs").is_null(),
            pl.col("expected_bowler_runs").is_null(),
            pl.col("expected_wicket_prob").is_null(),
        ).sum()
    ).item():
        raise ValueError("Context normalization produced missing expected values")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/pressure_deliveries.parquet"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/normalized_deliveries.parquet"),
    )
    args = parser.parse_args()
    normalized = build_context_expectations(pl.read_parquet(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    normalized.write_parquet(args.output)
    print(f"deliveries: {normalized.height:,}")
    print(f"context buckets: {normalized.select(CONTEXT_COLUMNS).unique().height:,}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
