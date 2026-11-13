import polars as pl
import pytest

from clutch_x.etl.normalizer import build_context_expectations


def test_context_expectations_include_format_season_innings_and_phase() -> None:
    deliveries = pl.DataFrame(
        {
            "match_format": ["T20I", "T20I", "T20I", "T20"],
            "season": ["2024", "2024", "2025", "2024"],
            "innings": [1, 1, 1, 1],
            "over_phase": ["powerplay", "powerplay", "powerplay", "powerplay"],
            "delivery_total_runs": [0, 4, 2, 6],
            "runs": [0, 4, 2, 6],
            "extras_type": ["None"] * 4,
            "extras1_runs": [0] * 4,
            "extras_2_runs": [0] * 4,
            "wicket_event": [0, 1, 0, 0],
        }
    )

    expected = build_context_expectations(deliveries)

    assert expected.height == deliveries.height
    assert expected.get_column("expected_runs").null_count() == 0
    assert expected.get_column("expected_batter_runs").null_count() == 0
    assert expected.get_column("expected_bowler_runs").null_count() == 0
    assert expected.get_column("expected_wicket_prob").null_count() == 0
    buckets = (
        expected.filter(pl.col("season") == "2024")
        .group_by("match_format")
        .agg(pl.col("context_bucket_deliveries").first())
    )
    assert dict(buckets.iter_rows()) == {"T20": 1, "T20I": 2}
    assert expected.get_column("expected_runs").to_list()[0] == pytest.approx(2.0)
