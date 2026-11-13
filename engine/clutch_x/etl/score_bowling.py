"""Export pressure bowling metrics and per-match audit impacts."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.baselines import compute_personal_baselines
from clutch_x.etl.bowling_metrics import compute_bowling_pressure_metrics


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
    _, bowling_baselines = compute_personal_baselines(deliveries)
    players, match_impacts = compute_bowling_pressure_metrics(
        deliveries,
        bowling_baselines,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    players.write_parquet(args.output_dir / "bowling_pressure_metrics.parquet")
    match_impacts.write_parquet(args.output_dir / "bowling_match_impacts.parquet")
    print(f"bowlers: {players.height:,}")
    print(f"high-pressure match audits: {match_impacts.height:,}")


if __name__ == "__main__":
    main()
