import polars as pl
import pytest

from clutch_x.report.build_report import _pressure_histogram, _validated_top10


def test_pressure_histogram_includes_upper_boundary_and_skips_nulls() -> None:
    histogram = _pressure_histogram(
        pl.DataFrame({"pressure_index": [0.0, 4.9, 5.0, 99.9, 100.0, None]})
    )

    assert len(histogram) == 20
    assert histogram[0]["count"] == 2
    assert histogram[1]["count"] == 1
    assert histogram[-1]["count"] == 2
    assert sum(item["count"] for item in histogram) == 5


def test_report_rejects_non_top10_rank_order(tmp_path) -> None:
    artifact = tmp_path / "top10.parquet"
    pl.DataFrame(
        {
            "rank": list(range(2, 12)),
            "player_id": list(range(1, 11)),
            "player_name": [f"Player {index}" for index in range(10)],
            "clutch_x_score": [100.0 - index for index in range(10)],
        }
    ).write_parquet(artifact)

    with pytest.raises(ValueError, match="strictly ordered"):
        _validated_top10(artifact)


def test_report_rejects_nonfinite_rank_metrics(tmp_path) -> None:
    artifact = tmp_path / "top10.parquet"
    pl.DataFrame(
        {
            "rank": list(range(1, 11)),
            "player_id": list(range(1, 11)),
            "player_name": [f"Player {index}" for index in range(10)],
            "clutch_x_score": [100.0, float("nan"), *[80.0 - index for index in range(8)]],
        }
    ).write_parquet(artifact)

    with pytest.raises(ValueError, match="non-finite"):
        _validated_top10(artifact)
