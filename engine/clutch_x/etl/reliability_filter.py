"""Export volume-qualified, reliability-adjusted player cohorts."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.reliability import (
    apply_batting_reliability,
    apply_bowling_reliability,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    batting = apply_batting_reliability(
        pl.read_parquet(args.input_dir / "batting_pressure_metrics.parquet"),
        pl.read_parquet(args.input_dir / "batting_match_impacts.parquet"),
    )
    bowling = apply_bowling_reliability(
        pl.read_parquet(args.input_dir / "bowling_pressure_metrics.parquet"),
        pl.read_parquet(args.input_dir / "bowling_match_impacts.parquet"),
    )
    batting.write_parquet(args.input_dir / "eligible_batters.parquet")
    bowling.write_parquet(args.input_dir / "eligible_bowlers.parquet")
    print(f"eligible batters: {batting.height:,}")
    print(f"eligible bowlers: {bowling.height:,}")


if __name__ == "__main__":
    main()
