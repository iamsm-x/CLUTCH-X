"""Compute player-specific performance profiles on normal-pressure balls."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.delivery_rules import (
    BOWLER_CREDITED_DISMISSALS,
    bowler_runs_conceded,
)


def compute_personal_baselines(
    deliveries: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return normal-pressure batting and bowling profiles by player ID."""
    required = {
        "is_high_pressure", "striker_id", "striker_name", "bowler_id", "bowler_name",
        "match_id", "innings", "extras_type", "runs", "is_four", "is_six",
        "delivery_total_runs", "legal_ball_event", "is_wicket", "dismissed_player_id",
        "dismissal_type", "extras1_runs", "extras_2_runs",
    }
    missing = required - set(deliveries.columns)
    if missing:
        raise ValueError(f"Baseline input missing columns: {', '.join(sorted(missing))}")

    normal = deliveries.filter(~pl.col("is_high_pressure"))
    extras = pl.col("extras_type").fill_null("").str.to_lowercase()
    batting = (
        normal.with_columns(
            (~extras.is_in(["wide"])).cast(pl.Int64).alias("_balls_faced"),
            pl.col("runs").fill_null(0).alias("_batter_runs"),
            (pl.col("is_four").fill_null(False) | pl.col("is_six").fill_null(False))
            .cast(pl.Int64)
            .alias("_boundaries"),
            (pl.col("delivery_total_runs") == 0).cast(pl.Int64).alias("_team_dots"),
            (
                pl.col("is_wicket").fill_null(False)
                & (pl.col("dismissed_player_id") == pl.col("striker_id"))
            )
            .cast(pl.Int64)
            .alias("_batter_dismissals"),
        )
        .group_by("striker_id")
        .agg(
            pl.col("striker_name").first().alias("player_name"),
            pl.col("_batter_runs").sum().alias("normal_batter_runs"),
            pl.col("_balls_faced").sum().alias("normal_balls_faced"),
            pl.col("_boundaries").sum().alias("normal_boundaries"),
            pl.col("_team_dots").sum().alias("normal_dot_balls"),
            pl.col("_batter_dismissals").sum().alias("normal_dismissals"),
            pl.col("match_id").n_unique().alias("normal_matches"),
            pl.struct("match_id", "innings").n_unique().alias("normal_innings"),
        )
        .with_columns(
            pl.when(pl.col("normal_balls_faced") > 0)
            .then(pl.col("normal_batter_runs") * 100 / pl.col("normal_balls_faced"))
            .otherwise(None)
            .alias("normal_strike_rate"),
            pl.when(pl.col("normal_balls_faced") > 0)
            .then(pl.col("normal_boundaries") / pl.col("normal_balls_faced"))
            .otherwise(None)
            .alias("normal_boundary_rate"),
            pl.when(pl.col("normal_balls_faced") > 0)
            .then(pl.col("normal_dot_balls") / pl.col("normal_balls_faced"))
            .otherwise(None)
            .alias("normal_dot_rate"),
            pl.when(pl.col("normal_dismissals") > 0)
            .then(pl.col("normal_balls_faced") / pl.col("normal_dismissals"))
            .otherwise(None)
            .alias("normal_balls_per_dismissal"),
            pl.when(pl.col("normal_balls_faced") > 0)
            .then(pl.col("normal_dismissals") / pl.col("normal_balls_faced"))
            .otherwise(None)
            .alias("normal_dismissal_rate"),
        )
        .rename({"striker_id": "player_id"})
        .sort("player_id")
    )

    dismissal_type = pl.col("dismissal_type").fill_null("").str.to_lowercase()
    bowler_wicket = (
        pl.col("is_wicket").fill_null(False)
        & dismissal_type.is_in(BOWLER_CREDITED_DISMISSALS)
    )
    bowling = (
        normal.with_columns(
            bowler_runs_conceded().alias("_bowler_runs_conceded"),
            pl.col("legal_ball_event").fill_null(0).alias("_legal_balls"),
            (
                (pl.col("delivery_total_runs") == 0)
                & (pl.col("legal_ball_event") == 1)
            )
            .cast(pl.Int64)
            .alias("_bowler_dots"),
            bowler_wicket.cast(pl.Int64).alias("_bowler_wickets"),
        )
        .group_by("bowler_id")
        .agg(
            pl.col("bowler_name").first().alias("player_name"),
            pl.col("_bowler_runs_conceded").sum().alias("normal_runs_conceded"),
            pl.col("_legal_balls").sum().alias("normal_legal_balls"),
            pl.col("_bowler_dots").sum().alias("normal_dot_balls"),
            pl.col("_bowler_wickets").sum().alias("normal_bowler_wickets"),
            pl.col("match_id").n_unique().alias("normal_matches"),
            pl.struct("match_id", "innings").n_unique().alias("normal_innings"),
        )
        .with_columns(
            pl.when(pl.col("normal_legal_balls") > 0)
            .then(pl.col("normal_runs_conceded") * 6 / pl.col("normal_legal_balls"))
            .otherwise(None)
            .alias("normal_economy"),
            pl.when(pl.col("normal_legal_balls") > 0)
            .then(pl.col("normal_dot_balls") / pl.col("normal_legal_balls"))
            .otherwise(None)
            .alias("normal_dot_rate"),
            pl.when(pl.col("normal_legal_balls") > 0)
            .then(pl.col("normal_bowler_wickets") * 24 / pl.col("normal_legal_balls"))
            .otherwise(None)
            .alias("normal_wickets_per_24_balls"),
        )
        .rename({"bowler_id": "player_id"})
        .sort("player_id")
    )
    return batting, bowling


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/normalized_deliveries.parquet"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    batting, bowling = compute_personal_baselines(pl.read_parquet(args.input))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    batting.write_parquet(args.output_dir / "batting_baselines.parquet")
    bowling.write_parquet(args.output_dir / "bowling_baselines.parquet")
    print(f"batters: {batting.height:,}")
    print(f"bowlers: {bowling.height:,}")


if __name__ == "__main__":
    main()
