"""Validate source CSV headers, value types, keys, and relationships."""

import argparse
import csv
from collections import Counter
from pathlib import Path

from clutch_x.etl.schemas import (
    BOOLEAN_COLUMNS,
    DATA_FILES,
    INTEGER_COLUMNS,
    NULLABLE_COLUMNS,
    SOURCE_CONTRACTS,
)


class DatasetValidationError(ValueError):
    """Raised when source data cannot safely enter the analytics pipeline."""


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"true", "1"}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise DatasetValidationError(f"{path}: missing CSV header")
            return reader.fieldnames, list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetValidationError(f"{path}: unable to read CSV: {exc}") from exc


def validate_data_dir(data_dir: Path) -> dict[str, int]:
    """Validate all source files and return their row counts."""
    issues: list[str] = []
    tables: dict[str, list[dict[str, str]]] = {}
    row_counts: dict[str, int] = {}

    for filename in DATA_FILES:
        path = data_dir / filename
        if not path.is_file():
            issues.append(f"{path}: required source file is missing")
            continue
        try:
            headers, rows = _read_csv(path)
        except DatasetValidationError as exc:
            issues.append(str(exc))
            continue

        missing_columns = set(SOURCE_CONTRACTS[filename].required_columns) - set(headers)
        if missing_columns:
            issues.append(f"{path}: missing columns: {', '.join(sorted(missing_columns))}")
            continue
        if not rows:
            issues.append(f"{path}: source file contains no data rows")
            continue

        tables[filename] = rows
        row_counts[filename] = len(rows)
        contract = SOURCE_CONTRACTS[filename]
        seen_keys: set[tuple[str, ...]] = set()
        for line_number, row in enumerate(rows, start=2):
            for column in contract.primary_key:
                if (
                    not row.get(column, "").strip()
                    and column not in NULLABLE_COLUMNS.get(filename, ())
                ):
                    issues.append(f"{path}:{line_number}: primary-key field {column} is empty")
                    break
            else:
                key = tuple(row[column].strip() for column in contract.primary_key)
                if key in seen_keys:
                    issues.append(
                        f"{path}:{line_number}: duplicate primary key "
                        + ", ".join(f"{name}={value}" for name, value in zip(contract.primary_key, key))
                    )
                seen_keys.add(key)

            for column in INTEGER_COLUMNS.get(filename, ()):
                value = row.get(column, "").strip()
                if not value and column in NULLABLE_COLUMNS.get(filename, ()):
                    continue
                try:
                    int(value)
                except ValueError:
                    issues.append(f"{path}:{line_number}: {column} must be an integer, got {value!r}")

            for column in BOOLEAN_COLUMNS.get(filename, ()):
                value = row.get(column, "").strip().lower()
                if not value and column in NULLABLE_COLUMNS.get(filename, ()):
                    continue
                if value not in {"true", "false", "0", "1"}:
                    issues.append(f"{path}:{line_number}: {column} must be boolean, got {value!r}")

            if len(issues) >= 100:
                issues.append("validation stopped after 100 errors")
                break

    if not issues and len(tables) == len(DATA_FILES):
        competitions = {row["comp_id"]: row for row in tables["competitions.csv"]}
        matches = {row["match_id"]: row for row in tables["matches.csv"]}
        match_ids = set(matches)
        comp_ids = set(competitions)
        relationships = (
            ("ball_by_ball.csv", "match_id", match_ids),
            ("playing_eleven.csv", "match_id", match_ids),
            ("matches.csv", "comp_id", comp_ids),
            ("teams.csv", "comp_id", comp_ids),
            ("competition_team_player_mapping.csv", "comp_id", comp_ids),
        )
        for filename, column, valid_values in relationships:
            missing = sorted({row[column] for row in tables[filename]} - valid_values)
            if missing:
                issues.append(
                    f"{data_dir / filename}: {len(missing)} distinct {column} values "
                    f"do not reference a known record (examples: {', '.join(missing[:5])})"
                )

        for row in tables["matches.csv"]:
            fmt = competitions[row["comp_id"]]["match_format"]
            if fmt not in {"T20", "T20I"}:
                issues.append(
                    f"{data_dir / 'matches.csv'}: match {row['match_id']} uses unsupported format {fmt!r}"
                )

        ball_counts = Counter(row["match_id"] for row in tables["ball_by_ball.csv"])
        if not ball_counts:
            issues.append(f"{data_dir / 'ball_by_ball.csv'}: no delivery records found")

    if issues:
        raise DatasetValidationError("\n".join(issues))
    return row_counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    args = parser.parse_args()
    try:
        counts = validate_data_dir(args.data_dir)
    except DatasetValidationError as exc:
        parser.exit(1, f"Source validation failed:\n{exc}\n")
    for filename, count in counts.items():
        print(f"OK {filename}: {count:,} rows")
    print("Source validation passed.")


if __name__ == "__main__":
    main()
