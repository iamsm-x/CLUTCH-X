"""Create the cleaned, metadata-enriched pre-delivery state artifact."""

import argparse
from pathlib import Path

from clutch_x.etl.clean_matches import clean_deliveries
from clutch_x.etl.enrich_deliveries import attach_pre_delivery_state, enrich_deliveries
from clutch_x.etl.load_sources import load_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("Data Pack"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    frames = load_sources(args.data_dir)
    frames["ball_by_ball"], exclusion_counts = clean_deliveries(frames)
    deliveries = attach_pre_delivery_state(enrich_deliveries(frames))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "delivery_states.parquet"
    deliveries.write_parquet(output)
    for key, value in exclusion_counts.items():
        print(f"{key}: {value:,}")
    print(f"state_rows: {deliveries.height:,}")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
