"""Build a methodology PDF directly from verified ranking artifacts."""

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import polars as pl

from clutch_x.etl.ranking_audit import MIN_SPLIT_HALF_RHO, validate_top10
from clutch_x.etl.validate_pressure import (
    MAX_HIGH_PRESSURE_SHARE,
    MAX_P_VALUE,
    MIN_HIGH_PRESSURE_SHARE,
    audit_pressure_dataset,
)

PACKAGE_DIR = Path(__file__).parent
SOURCE_FILES = (
    "ball_by_ball.csv",
    "matches.csv",
    "competitions.csv",
    "playing_eleven.csv",
    "teams.csv",
    "competition_team_player_mapping.csv",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_top10(path: Path) -> pl.DataFrame:
    frame = pl.read_parquet(path)
    validate_top10(frame)
    float_columns = [
        name
        for name, dtype in frame.schema.items()
        if dtype in (pl.Float32, pl.Float64)
    ]
    nonfinite = frame.select(
        pl.any_horizontal(
            *(
                pl.col(name).is_nan() | pl.col(name).is_infinite()
                for name in float_columns
            )
        ).any()
    ).item()
    if nonfinite:
        raise ValueError(f"{path} contains non-finite numeric values")
    return frame


def _rank_rows(frame: pl.DataFrame, columns: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {name: row[name] for name in columns}
        for row in frame.select(columns).to_dicts()
    ]


def _pressure_histogram(deliveries: pl.DataFrame) -> list[dict[str, Any]]:
    counts = [0] * 20
    for value in deliveries.get_column("pressure_index").to_list():
        if value is not None and math.isfinite(value):
            counts[min(int(value // 5), 19)] += 1
    maximum = max(counts, default=0) or 1
    return [
        {
            "label": f"{index * 5:02d}-{index * 5 + 4:02d}",
            "count": count,
            "bar_width_pt": max(1, round(count / maximum * 150)),
        }
        for index, count in enumerate(counts)
    ]


def _exposure_summary(path: Path) -> list[dict[str, Any]]:
    exposure = pl.read_parquet(path)
    summary = (
        exposure.group_by(["competition_type", "innings"])
        .agg(
            pl.col("player_id").n_unique().alias("represented_players"),
            pl.col("high_pressure_volume").sum().alias("high_pressure_volume"),
        )
        .sort(["competition_type", "innings"])
    )
    return summary.to_dicts()


def _report_data(processed_dir: Path, data_dir: Path) -> dict[str, Any]:
    batting = _validated_top10(processed_dir / "top10_batters.parquet")
    bowling = _validated_top10(processed_dir / "top10_bowlers.parquet")
    deliveries = pl.read_parquet(processed_dir / "normalized_deliveries.parquet")
    audit = pl.read_parquet(processed_dir / "ranking_audit_summary.parquet")
    audit_by_discipline = {
        row["discipline"]: row for row in audit.to_dicts()
    }
    if set(audit_by_discipline) != {"batting", "bowling"}:
        raise ValueError("Ranking audit summary must contain batting and bowling rows")
    split_half = [
        {
            "discipline": discipline,
            "rho": float(audit_by_discipline[discipline]["split_half_rho"]),
            "eligible_players": int(
                audit_by_discipline[discipline]["eligible_players"]
            ),
            "target": MIN_SPLIT_HALF_RHO,
            "meets_target": bool(
                audit_by_discipline[discipline]["split_half_rho"]
                >= MIN_SPLIT_HALF_RHO
            ),
        }
        for discipline in ("batting", "bowling")
    ]
    pressure_audit = audit_pressure_dataset(deliveries)
    if pressure_audit["high_pressure_share"] < MIN_HIGH_PRESSURE_SHARE or (
        pressure_audit["high_pressure_share"] > MAX_HIGH_PRESSURE_SHARE
    ):
        pressure_audit["passes_acceptance"] = False

    raw_sources = [
        {"name": name, "sha256": _sha256(data_dir / name)}
        for name in SOURCE_FILES
        if (data_dir / name).is_file()
    ]
    artifact_names = (
        "top10_batters.parquet",
        "top10_bowlers.parquet",
        "ranking_audit_summary.parquet",
    )
    artifact_hashes = [
        {"name": name, "sha256": _sha256(processed_dir / name)}
        for name in artifact_names
    ]
    season_values = deliveries.get_column("season").drop_nulls().unique().sort()
    competitions = (
        deliveries.get_column("competition_name").drop_nulls().n_unique()
    )
    high_pressure_share = float(pressure_audit["high_pressure_share"])

    return {
        "title": "CLUTCH-X",
        "subtitle": "A reproducible methodology for T20 pressure analytics",
        "first_season": str(season_values[0]) if season_values.len() else "Unknown",
        "latest_season": str(season_values[-1]) if season_values.len() else "Unknown",
        "delivery_count": deliveries.height,
        "match_count": deliveries.get_column("match_id").n_unique(),
        "competition_count": competitions,
        "eligible_batters": pl.read_parquet(
            processed_dir / "eligible_batters.parquet"
        ).height,
        "eligible_bowlers": pl.read_parquet(
            processed_dir / "eligible_bowlers.parquet"
        ).height,
        "high_pressure_share": high_pressure_share,
        "pressure_acceptance": bool(pressure_audit["passes_acceptance"]),
        "pressure_audit": {
            key: value
            for key, value in pressure_audit.items()
            if key != "passes_acceptance"
        },
        "pressure_histogram": _pressure_histogram(deliveries),
        "split_half": split_half,
        "rankings_meet_stability_target": all(
            item["meets_target"] for item in split_half
        ),
        "batting": _rank_rows(
            batting,
            (
                "rank",
                "player_id",
                "player_name",
                "high_pressure_balls_faced",
                "high_pressure_matches",
                "normal_strike_rate",
                "high_pressure_strike_rate",
                "strike_rate_delta",
                "prae_per_100",
                "positive_impact_rate",
                "baseline_rating",
                "pressure_rating",
                "net_clutch_delta",
                "clutch_x_score",
                "reliability_weight",
            ),
        ),
        "bowling": _rank_rows(
            bowling,
            (
                "rank",
                "player_id",
                "player_name",
                "high_pressure_legal_balls",
                "high_pressure_matches",
                "normal_economy",
                "high_pressure_economy",
                "economy_delta",
                "prsae_per_over",
                "high_pressure_dot_rate",
                "high_pressure_wickets",
                "positive_impact_rate",
                "baseline_rating",
                "pressure_rating",
                "net_clutch_delta",
                "clutch_x_score",
                "reliability_weight",
            ),
        ),
        "batting_exposure": _exposure_summary(
            processed_dir / "batting_top10_exposure.parquet"
        ),
        "bowling_exposure": _exposure_summary(
            processed_dir / "bowling_top10_exposure.parquet"
        ),
        "source_files": raw_sources,
        "artifact_hashes": artifact_hashes,
    }


def build_report(
    *,
    processed_dir: Path,
    data_dir: Path,
    output_dir: Path,
    typst_executable: str | None = None,
) -> Path:
    """Write a data snapshot and compile the Typst report PDF."""
    data = _report_data(processed_dir, data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "report-data.json"
    template_path = output_dir / "clutch_x_report.typ"
    pdf_path = output_dir / "clutch_x_methodology.pdf"
    data_path.write_text(
        json.dumps(data, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(PACKAGE_DIR / "clutch_x_report.typ", template_path)

    executable = typst_executable or shutil.which("typst")
    if not executable:
        raise RuntimeError(
            "Typst CLI was not found. Install Typst, then rerun "
            "`python -m clutch_x.report.build_report`."
        )
    report_root = output_dir.resolve()
    subprocess.run(
        [
            executable,
            "compile",
            "--root",
            str(report_root),
            str(template_path.resolve()),
            str(pdf_path.resolve()),
        ],
        cwd=report_root,
        check=True,
    )
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    output = build_report(
        processed_dir=args.processed_dir,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    )
    print(f"Methodology report written to {output}")


if __name__ == "__main__":
    main()
