import polars as pl

from clutch_x.etl.validate_pressure import audit_pressure_dataset


def test_pressure_audit_checks_share_and_statistical_separation() -> None:
    high_rows = 200
    normal_rows = 800
    high_runs = [0, 0, 0, 1, 2, 4, 6, 8, 12, 16] * 20
    normal_runs = [0, 0, 0, 0, 1, 1, 2, 2, 3, 4] * 80
    high_wickets = [1] * 30 + [0] * (high_rows - 30)
    normal_wickets = [1] * 24 + [0] * (normal_rows - 24)
    frame = pl.DataFrame(
        {
            "is_high_pressure": [True] * high_rows + [False] * normal_rows,
            "delivery_total_runs": high_runs + normal_runs,
            "wicket_event": high_wickets + normal_wickets,
        }
    )

    result = audit_pressure_dataset(frame)

    assert result["high_pressure_share"] == 0.2
    assert result["passes_acceptance"] is True
