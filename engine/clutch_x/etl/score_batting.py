"""Export pressure batting metrics and per-match audit impacts."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.batting_metrics import compute_batting_pressure_metrics
from clutch_x.etl.baselines import compute_personal_baselines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/normalized_deliveries.parquet"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    deliveries = pl.read_parquet(args.input)
    batting_baselines, _ = compute_personal_baselines(deliveries)
    players, match_impacts = compute_batting_pressure_metrics(
        deliveries,
        batting_baselines,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    players.write_parquet(args.output_dir / "batting_pressure_metrics.parquet")
    match_impacts.write_parquet(args.output_dir / "batting_match_impacts.parquet")
    print(f"batters: {players.height:,}")
    print(f"high-pressure match audits: {match_impacts.height:,}")


if __name__ == "__main__":
    main()
