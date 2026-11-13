"""Load validated source CSVs into typed Polars DataFrames."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.schemas import BOOLEAN_COLUMNS, DATA_FILES, INTEGER_COLUMNS
from clutch_x.etl.validate_sources import validate_data_dir


def load_sources(data_dir: Path) -> dict[str, pl.DataFrame]:
    """Validate and load all source CSVs with stable key-column types."""
    validate_data_dir(data_dir)
    frames: dict[str, pl.DataFrame] = {}
    for filename in DATA_FILES:
        integer_columns = set(INTEGER_COLUMNS.get(filename, ()))
        boolean_columns = set(BOOLEAN_COLUMNS.get(filename, ()))
        overrides = {column: pl.Int64 for column in integer_columns}
        overrides.update({column: pl.String for column in boolean_columns})
        frame = pl.read_csv(
            data_dir / filename,
            encoding="utf8",
            null_values=[""],
            schema_overrides=overrides,
            infer_schema_length=10_000,
        )
        if boolean_columns:
            frame = frame.with_columns(
                pl.when(pl.col(column).str.to_lowercase().is_in(["true", "1"]))
                .then(pl.lit(True))
                .when(pl.col(column).str.to_lowercase().is_in(["false", "0"]))
                .then(pl.lit(False))
                .otherwise(pl.lit(None, dtype=pl.Boolean))
                .alias(column)
                for column in boolean_columns
            )
        frames[filename.removesuffix(".csv")] = frame
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    args = parser.parse_args()
    for name, frame in load_sources(args.data_dir).items():
        print(f"Loaded {name}: {frame.height:,} rows, {frame.width} columns")


if __name__ == "__main__":
    main()
