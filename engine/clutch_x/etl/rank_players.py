"""Export deterministic Top-10 pressure batter and bowler leaderboards."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.leaderboards import build_batting_top10, build_bowling_top10


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    batters = build_batting_top10(
        pl.read_parquet(args.input_dir / "eligible_batters.parquet")
    )
    bowlers = build_bowling_top10(
        pl.read_parquet(args.input_dir / "eligible_bowlers.parquet")
    )
    batters.write_parquet(args.input_dir / "top10_batters.parquet")
    bowlers.write_parquet(args.input_dir / "top10_bowlers.parquet")
    print("Top-10 pressure batters")
    print(batters.select("rank", "player_id", "player_name", "clutch_x_score"))
    print("Top-10 pressure bowlers")
    print(bowlers.select("rank", "player_id", "player_name", "clutch_x_score"))


if __name__ == "__main__":
    main()
