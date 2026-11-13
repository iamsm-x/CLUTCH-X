"""Build a queryable DuckDB database from processed Parquet artifacts."""

import argparse
import hashlib
import re
from pathlib import Path

import duckdb

from clutch_x.etl.schemas import DATA_FILES

STORE_SCHEMA_VERSION = "1"
TABLE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_rows(paths: list[Path], root: Path) -> list[tuple[str, str, int]]:
    return [
        (path.relative_to(root).as_posix(), _sha256(path), path.stat().st_size)
        for path in paths
    ]


def build_analytical_store(
    processed_dir: Path,
    store_path: Path,
    data_dir: Path,
) -> list[tuple[str, int]]:
    """Create/rebuild one DuckDB table per Parquet file and source manifests."""
    parquet_files = sorted(processed_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No processed Parquet files found in {processed_dir}")
    invalid_names = [
        path.name
        for path in parquet_files
        if not TABLE_NAME_PATTERN.fullmatch(path.stem)
    ]
    if invalid_names:
        raise ValueError(f"Invalid Parquet artifact table names: {invalid_names}")

    source_files = [data_dir / name for name in DATA_FILES]
    missing_sources = [path for path in source_files if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(
            "Missing source files for provenance: "
            + ", ".join(str(path) for path in missing_sources)
        )

    config_dir = Path(__file__).parent
    config_files = sorted(config_dir.glob("*.py"))
    source_manifest = _manifest_rows(source_files, data_dir)
    configuration_manifest = _manifest_rows(config_files, config_dir.parent.parent.parent)
    store_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(store_path)) as connection:
        connection.execute("BEGIN TRANSACTION")
        artifact_rows = []
        for parquet_file in parquet_files:
            table_name = parquet_file.stem
            quoted_table = f'"{table_name}"'
            connection.execute(
                f"CREATE OR REPLACE TABLE {quoted_table} AS "
                "SELECT * FROM read_parquet(?)",
                [str(parquet_file)],
            )
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {quoted_table}"
            ).fetchone()[0]
            artifact_rows.append((table_name, parquet_file.name, row_count))

        connection.execute(
            "CREATE OR REPLACE TABLE artifact_metadata "
            "(key VARCHAR PRIMARY KEY, value VARCHAR NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO artifact_metadata VALUES (?, ?)",
            [
                ("store_schema_version", STORE_SCHEMA_VERSION),
                ("parquet_artifact_count", str(len(artifact_rows))),
            ],
        )
        connection.execute(
            "CREATE OR REPLACE TABLE artifact_catalog "
            "(table_name VARCHAR PRIMARY KEY, file_name VARCHAR NOT NULL, "
            "row_count BIGINT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO artifact_catalog VALUES (?, ?, ?)", artifact_rows
        )
        connection.execute(
            "CREATE OR REPLACE TABLE source_manifest "
            "(file_name VARCHAR PRIMARY KEY, sha256 VARCHAR NOT NULL, "
            "size_bytes BIGINT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO source_manifest VALUES (?, ?, ?)", source_manifest
        )
        connection.execute(
            "CREATE OR REPLACE TABLE configuration_manifest "
            "(file_name VARCHAR PRIMARY KEY, sha256 VARCHAR NOT NULL, "
            "size_bytes BIGINT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO configuration_manifest VALUES (?, ?, ?)",
            configuration_manifest,
        )
        connection.execute("COMMIT")
    return artifact_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--output",
        type=Path,
        help="DuckDB output path (default: <input-dir>/clutch_x.duckdb)",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    args = parser.parse_args()
    store_path = args.output or args.input_dir / "clutch_x.duckdb"
    artifacts = build_analytical_store(args.input_dir, store_path, args.data_dir)
    print(f"Wrote {len(artifacts)} tables to {store_path}")


if __name__ == "__main__":
    main()
