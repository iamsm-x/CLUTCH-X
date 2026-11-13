"""Score the reconstructed state artifact with the Pressure Index."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.pressure_index import compute_pressure_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/delivery_states.parquet"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/pressure_deliveries.parquet"),
    )
    args = parser.parse_args()
    scored = compute_pressure_index(pl.read_parquet(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scored.write_parquet(args.output)
    share = scored.get_column("is_high_pressure").mean() * 100
    print(f"deliveries: {scored.height:,}")
    print(f"high_pressure_share: {share:.2f}%")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
