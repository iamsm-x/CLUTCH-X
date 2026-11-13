"""Remove Super Over deliveries and abandoned matches with too little play."""

import argparse
from pathlib import Path

import polars as pl

from clutch_x.etl.delivery_rules import is_legal_delivery
from clutch_x.etl.load_sources import load_sources

ABANDONED_RESULT_TERMS = ("abandoned", "no result")
MINIMUM_PLAY_LEGAL_BALLS = 30


def clean_deliveries(
    frames: dict[str, pl.DataFrame],
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Filter invalid match phases and report deterministic exclusion counts."""
    deliveries = frames["ball_by_ball"]
    in_scope_competitions = frames["competitions"].filter(
        (pl.col("match_format") == "T20I")
        | (
            (pl.col("match_format") == "T20")
            & pl.col("comp_name").str.contains(r"(?i)\bIPL\b")
        )
    ).select("comp_id")
    in_scope_matches = (
        frames["matches"]
        .join(in_scope_competitions, on="comp_id", how="semi")
        .select("match_id")
    )
    excluded_out_of_scope = deliveries.join(
        in_scope_matches,
        on="match_id",
        how="anti",
    ).height
    deliveries = deliveries.join(in_scope_matches, on="match_id", how="semi")
    matches = frames["matches"].join(
        in_scope_matches,
        on="match_id",
        how="semi",
    )

    excluded_super_over = deliveries.filter(pl.col("innings") > 2).height
    legal_by_match = (
        deliveries
        .filter(is_legal_delivery())
        .group_by("match_id")
        .len(name="legal_balls")
    )
    abandoned_ids = (
        matches
        .filter(
            pl.col("result")
            .fill_null("")
            .str.to_lowercase()
            .str.contains("|".join(ABANDONED_RESULT_TERMS))
        )
        .select("match_id")
        .join(legal_by_match, on="match_id", how="left")
        .filter(pl.col("legal_balls").fill_null(0) < MINIMUM_PLAY_LEGAL_BALLS)
        .select("match_id")
    )
    excluded_abandoned = deliveries.join(abandoned_ids, on="match_id", how="semi").height
    cleaned = deliveries.filter(pl.col("innings") <= 2).join(
        abandoned_ids,
        on="match_id",
        how="anti",
    )
    return cleaned, {
        "input_deliveries": frames["ball_by_ball"].height,
        "excluded_out_of_scope_deliveries": excluded_out_of_scope,
        "excluded_super_over_deliveries": excluded_super_over,
        "excluded_insufficient_play_deliveries": excluded_abandoned,
        "output_deliveries": cleaned.height,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    frames = load_sources(args.data_dir)
    cleaned, counts = clean_deliveries(frames)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "clean_deliveries.parquet"
    cleaned.write_parquet(output)
    for key, value in counts.items():
        print(f"{key}: {value:,}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
