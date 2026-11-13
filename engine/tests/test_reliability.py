import polars as pl
import pytest

from clutch_x.etl.reliability import apply_batting_reliability


def test_reliability_enforces_volume_and_shrinks_toward_eligible_peer_mean() -> None:
    metrics = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_name": ["Steady", "Volatile", "Low volume"],
            "high_pressure_balls_faced": [200, 150, 149],
            "high_pressure_matches": [10, 10, 20],
            "prae_per_100": [5.0, -3.0, 100.0],
            "strike_rate_delta": [10.0, -10.0, 1000.0],
            "boundary_rate_delta": [0.2, -0.2, 1.0],
            "dot_rate_improvement": [0.1, -0.1, 1.0],
            "wicket_preservation_delta": [5.0, -5.0, 100.0],
        }
    )
    impact_rows = []
    for player_id, impacts in [(1, [1.0] * 10), (2, [10.0, -10.0] + [0.0] * 8)]:
        impact_rows.extend(
            {
                "player_id": player_id,
                "match_id": match_id,
                "match_net_impact": impact,
                "high_pressure_balls_faced": 100,
            }
            for match_id, impact in enumerate(impacts)
        )
    impacts = pl.DataFrame(impact_rows)

    eligible = apply_batting_reliability(metrics, impacts)

    assert eligible.get_column("player_id").to_list() == [1, 2]
    steady = eligible.filter(pl.col("player_id") == 1).row(0, named=True)
    volatile = eligible.filter(pl.col("player_id") == 2).row(0, named=True)
    assert steady["reliability_weight"] == pytest.approx(200 / 350)
    assert steady["shrunk_prae_per_100"] == pytest.approx(23 / 7)
    assert steady["shrunk_strike_rate_delta"] == pytest.approx(40 / 7)
    assert steady["volatility_adjusted_prae"] == pytest.approx(1.0)
    assert volatile["volatility_adjusted_prae"] < steady["volatility_adjusted_prae"]
