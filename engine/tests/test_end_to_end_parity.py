import duckdb
import polars as pl

from clutch_x.api.main import leaderboard
from clutch_x.api.schemas import AnalyticsFilters
from clutch_x.etl.batting_metrics import compute_batting_pressure_metrics
from clutch_x.etl.baselines import compute_personal_baselines
from clutch_x.etl.bowling_metrics import compute_bowling_pressure_metrics
from clutch_x.etl.leaderboards import build_batting_top10, build_bowling_top10
from clutch_x.etl.reliability import apply_batting_reliability, apply_bowling_reliability
from clutch_x.report.build_report import _report_data


def _synthetic_deliveries() -> pl.DataFrame:
    rows = []
    for match_id in range(1, 11):
        for player_id in range(1, 11):
            for ball_index in range(15):
                batter_runs = (player_id + ball_index + match_id) % 7
                rows.append(
                    {
                        "competition_name": "Indian Premier League (IPL)",
                        "match_format": "T20",
                        "season": "2024",
                        "match_id": match_id,
                        "innings": 1,
                        "overid": 15,
                        "knock_out": False,
                        "pressure_index": 70.0,
                        "is_high_pressure": True,
                        "striker_id": player_id,
                        "striker_name": f"Player {player_id}",
                        "bowler_id": (player_id + ball_index - 1) % 10 + 1,
                        "bowler_name": f"Player {(player_id + ball_index - 1) % 10 + 1}",
                        "extras_type": "",
                        "runs": batter_runs,
                        "is_four": batter_runs == 4,
                        "is_six": batter_runs == 6,
                        "delivery_total_runs": batter_runs,
                        "expected_batter_runs": 1.0 + player_id % 3,
                        "expected_bowler_runs": 1.0 + ball_index % 2,
                        "is_wicket": ball_index == 0 and player_id == 1,
                        "dismissed_player_id": (
                            99 if ball_index == 0 and player_id == 1 else None
                        ),
                        "dismissal_type": (
                            "run out" if ball_index == 0 and player_id == 1 else ""
                        ),
                        "legal_ball_event": 1,
                        "batting_order": player_id,
                        "extras1_runs": 0,
                        "extras_2_runs": 0,
                        "wicket_event": int(ball_index == 0 and player_id == 1),
                    }
                )
        for player_id in range(1, 11):
            batter_runs = (player_id + match_id) % 5
            rows.append(
                {
                    "competition_name": "Indian Premier League (IPL)",
                    "match_format": "T20",
                    "season": "2024",
                    "match_id": match_id,
                    "innings": 1,
                    "overid": 10,
                    "knock_out": False,
                    "pressure_index": 20.0,
                    "is_high_pressure": False,
                    "striker_id": player_id,
                    "striker_name": f"Player {player_id}",
                    "bowler_id": player_id,
                    "bowler_name": f"Player {player_id}",
                    "extras_type": "",
                    "runs": batter_runs,
                    "is_four": batter_runs == 4,
                    "is_six": False,
                    "delivery_total_runs": batter_runs,
                    "expected_batter_runs": 1.0,
                    "expected_bowler_runs": 1.0,
                    "is_wicket": False,
                    "dismissed_player_id": None,
                    "dismissal_type": "",
                    "legal_ball_event": 1,
                    "batting_order": player_id,
                    "extras1_runs": 0,
                    "extras_2_runs": 0,
                    "wicket_event": 0,
                }
            )
    return pl.DataFrame(rows)


def test_api_and_report_preserve_batch_top10_ranks_and_player_ids(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    source_dir = tmp_path / "source"
    processed_dir.mkdir()
    source_dir.mkdir()
    deliveries = _synthetic_deliveries()

    batting_baselines, bowling_baselines = compute_personal_baselines(deliveries)
    batting_metrics, batting_impacts = compute_batting_pressure_metrics(
        deliveries, batting_baselines
    )
    bowling_metrics, bowling_impacts = compute_bowling_pressure_metrics(
        deliveries, bowling_baselines
    )
    batting_eligible = apply_batting_reliability(batting_metrics, batting_impacts)
    bowling_eligible = apply_bowling_reliability(bowling_metrics, bowling_impacts)
    batting_rankings = build_batting_top10(batting_eligible)
    bowling_rankings = build_bowling_top10(bowling_eligible)

    batting_rankings.write_parquet(processed_dir / "top10_batters.parquet")
    bowling_rankings.write_parquet(processed_dir / "top10_bowlers.parquet")
    batting_eligible.write_parquet(processed_dir / "eligible_batters.parquet")
    bowling_eligible.write_parquet(processed_dir / "eligible_bowlers.parquet")
    deliveries.write_parquet(processed_dir / "normalized_deliveries.parquet")
    pl.DataFrame(
        {
            "discipline": ["batting", "bowling"],
            "split_half_rho": [0.2, 0.3],
            "eligible_players": [10, 10],
            "target_rho": [0.65, 0.65],
            "meets_target": [False, False],
        }
    ).write_parquet(processed_dir / "ranking_audit_summary.parquet")
    for discipline, rankings, volume in (
        ("batting", batting_rankings, "high_pressure_balls_faced"),
        ("bowling", bowling_rankings, "high_pressure_legal_balls"),
    ):
        pl.DataFrame(
            {
                "player_id": rankings.get_column("player_id"),
                "competition_type": ["IPL"] * 10,
                "innings": [1] * 10,
                "high_pressure_volume": rankings.get_column(volume),
            }
        ).write_parquet(processed_dir / f"{discipline}_top10_exposure.parquet")

    parquet_path = processed_dir / "normalized_deliveries.parquet"
    with duckdb.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE normalized_deliveries AS SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        )
        filters = AnalyticsFilters()
        api_batting = leaderboard("batting", filters, connection)
        api_bowling = leaderboard("bowling", filters, connection)

    report_data = _report_data(processed_dir, source_dir)
    for discipline, batch, api_result, report_rows in (
        ("batting", batting_rankings, api_batting, report_data["batting"]),
        ("bowling", bowling_rankings, api_bowling, report_data["bowling"]),
    ):
        expected = batch.select("rank", "player_id", "clutch_x_score").to_dicts()
        actual_api = [
            {
                "rank": entry.rank,
                "player_id": entry.player_id,
                "clutch_x_score": entry.clutch_x_score,
            }
            for entry in api_result.entries
        ]
        actual_report = [
            {
                "rank": row["rank"],
                "player_id": row["player_id"],
                "clutch_x_score": row["clutch_x_score"],
            }
            for row in report_rows
        ]

        assert api_result.discipline == discipline
        assert actual_api == expected
        assert actual_report == expected
