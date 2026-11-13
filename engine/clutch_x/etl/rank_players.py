"""Export deterministic Top-10 pressure batter and bowler leaderboards."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.leaderboards import (
    build_batting_top10,
    build_bowling_top10,
    build_batting_rankings,
    build_bowling_rankings,
)

RANKING_THRESHOLDS = (100, 150, 200, 250, 300)


def _write_threshold_rankings(
    eligible: pl.DataFrame,
    *,
    volume_column: str,
    builder,
    output_dir: Path,
    discipline: str,
) -> None:
    for threshold in RANKING_THRESHOLDS:
        filtered = eligible.filter(pl.col(volume_column) >= threshold)
        if filtered.height < 10:
            raise ValueError(
                f"Only {filtered.height} eligible {discipline} players meet "
                f"the {threshold}-ball threshold"
            )
        builder(filtered).write_parquet(
            output_dir / f"top10_{discipline}_min_{threshold}.parquet"
        )


def _write_threshold_scatter(
    eligible: pl.DataFrame,
    *,
    volume_column: str,
    builder,
    output_dir: Path,
    discipline: str,
) -> None:
    for threshold in RANKING_THRESHOLDS:
        filtered = eligible.filter(pl.col(volume_column) >= threshold)
        builder(filtered).write_parquet(
            output_dir / f"{discipline}_scatter_min_{threshold}.parquet"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    eligible_batters = pl.read_parquet(args.input_dir / "eligible_batters.parquet")
    eligible_bowlers = pl.read_parquet(args.input_dir / "eligible_bowlers.parquet")
    batters = build_batting_top10(eligible_batters)
    bowlers = build_bowling_top10(eligible_bowlers)
    batters.write_parquet(args.input_dir / "top10_batters.parquet")
    bowlers.write_parquet(args.input_dir / "top10_bowlers.parquet")
    _write_threshold_rankings(
        eligible_batters,
        volume_column="high_pressure_balls_faced",
        builder=build_batting_top10,
        output_dir=args.input_dir,
        discipline="batters",
    )
    _write_threshold_rankings(
        eligible_bowlers,
        volume_column="high_pressure_legal_balls",
        builder=build_bowling_top10,
        output_dir=args.input_dir,
        discipline="bowlers",
    )
    _write_threshold_scatter(
        eligible_batters,
        volume_column="high_pressure_balls_faced",
        builder=build_batting_rankings,
        output_dir=args.input_dir,
        discipline="batting",
    )
    _write_threshold_scatter(
        eligible_bowlers,
        volume_column="high_pressure_legal_balls",
        builder=build_bowling_rankings,
        output_dir=args.input_dir,
        discipline="bowling",
    )
    print("Top-10 pressure batters")
    print(batters.select("rank", "player_id", "player_name", "clutch_x_score"))
    print("Top-10 pressure bowlers")
    print(bowlers.select("rank", "player_id", "player_name", "clutch_x_score"))


if __name__ == "__main__":
    main()
