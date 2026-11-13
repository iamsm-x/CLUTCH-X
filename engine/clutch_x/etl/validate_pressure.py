"""Audit pressure regime coverage and statistical separation."""

import argparse
from pathlib import Path

from scipy.stats import chi2_contingency, levene
import polars as pl

MIN_HIGH_PRESSURE_SHARE = 0.15
MAX_HIGH_PRESSURE_SHARE = 0.25
MAX_P_VALUE = 0.01


def audit_pressure_dataset(deliveries: pl.DataFrame) -> dict[str, float | bool]:
    """Measure KPI coverage, wicket-rate shift, and scoring-variance shift."""
    high = deliveries.filter(pl.col("is_high_pressure"))
    normal = deliveries.filter(~pl.col("is_high_pressure"))
    if high.is_empty() or normal.is_empty():
        raise ValueError("Both pressure regimes need deliveries for the statistical audit")

    high_wickets = high.get_column("wicket_event")
    normal_wickets = normal.get_column("wicket_event")
    wicket_table = [
        [int((high_wickets > 0).sum()), int((high_wickets == 0).sum())],
        [int((normal_wickets > 0).sum()), int((normal_wickets == 0).sum())],
    ]
    wicket_p_value = float(chi2_contingency(wicket_table).pvalue)
    scoring_variance_p_value = float(
        levene(
            high.get_column("delivery_total_runs").to_numpy(),
            normal.get_column("delivery_total_runs").to_numpy(),
            center="median",
        ).pvalue
    )
    high_share = high.height / deliveries.height
    high_wicket_rate = wicket_table[0][0] / high.height
    normal_wicket_rate = wicket_table[1][0] / normal.height

    return {
        "high_pressure_share": high_share,
        "high_pressure_wicket_rate": high_wicket_rate,
        "normal_wicket_rate": normal_wicket_rate,
        "wicket_rate_p_value": wicket_p_value,
        "high_pressure_run_variance": float(
            high.get_column("delivery_total_runs").var()
        ),
        "normal_run_variance": float(
            normal.get_column("delivery_total_runs").var()
        ),
        "run_variance_p_value": scoring_variance_p_value,
        "passes_acceptance": (
            MIN_HIGH_PRESSURE_SHARE <= high_share <= MAX_HIGH_PRESSURE_SHARE
            and wicket_p_value < MAX_P_VALUE
            and scoring_variance_p_value < MAX_P_VALUE
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/pressure_deliveries.parquet"),
    )
    args = parser.parse_args()
    result = audit_pressure_dataset(pl.read_parquet(args.input))
    for key, value in result.items():
        if isinstance(value, float) and "p_value" not in key:
            print(f"{key}: {value:.4%}" if "rate" in key or "share" in key else f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")
    if not result["passes_acceptance"]:
        raise SystemExit("Pressure Index acceptance checks failed")


if __name__ == "__main__":
    main()
