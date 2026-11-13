"""Audit leaderboard integrity, competitive exposure, and split-half stability."""

import argparse
from pathlib import Path

import polars as pl
from scipy.stats import spearmanr

MIN_SPLIT_HALF_RHO = 0.65


def validate_top10(leaderboard: pl.DataFrame) -> None:
    """Raise when a leaderboard is not exactly ranks 1–10 with unique players."""
    if leaderboard.height != 10:
        raise ValueError(f"Expected 10 leaderboard rows, received {leaderboard.height}")
    if leaderboard.get_column("rank").to_list() != list(range(1, 11)):
        raise ValueError("Leaderboard ranks must be strictly ordered 1 through 10")
    if leaderboard.get_column("player_id").n_unique() != 10:
        raise ValueError("Leaderboard contains duplicate player IDs")
    scores = leaderboard.get_column("clutch_x_score").to_list()
    if any(score is None for score in scores):
        raise ValueError("Leaderboard contains missing Clutch-X scores")
    if any(left < right for left, right in zip(scores, scores[1:])):
        raise ValueError("Leaderboard scores are not in descending rank order")


def split_half_rank_stability(
    match_impacts: pl.DataFrame,
    deliveries: pl.DataFrame,
    *,
    impact_column: str,
    balls_column: str,
    scale: float,
) -> tuple[float, int]:
    """Alternate each player's dated match appearances into odd/even halves."""
    match_dates = deliveries.select("match_id", "match_date").unique()
    dated = (
        match_impacts.filter(pl.col(balls_column) > 0)
        .join(match_dates, on="match_id", how="left", validate="m:1")
        .sort(["player_id", "match_date", "match_id"])
    )
    halves: dict[tuple[int, str], list[float]] = {}
    current_player = None
    appearance_index = 0
    for row in dated.select("player_id", impact_column, balls_column).iter_rows():
        player_id, impact, balls = row
        if player_id != current_player:
            current_player = player_id
            appearance_index = 0
        half = "odd" if appearance_index % 2 == 0 else "even"
        total = halves.setdefault((player_id, half), [0.0, 0.0])
        total[0] += float(impact)
        total[1] += float(balls)
        appearance_index += 1

    odd_scores = []
    even_scores = []
    for player_id in sorted({key[0] for key in halves}):
        odd = halves.get((player_id, "odd"), [])
        even = halves.get((player_id, "even"), [])
        if odd and even and odd[1] > 0 and even[1] > 0:
            odd_scores.append(odd[0] * scale / odd[1])
            even_scores.append(even[0] * scale / even[1])
    if len(odd_scores) < 2:
        return float("nan"), len(odd_scores)
    return float(spearmanr(odd_scores, even_scores).statistic), len(odd_scores)


def _top10_exposure(
    deliveries: pl.DataFrame,
    leaderboard: pl.DataFrame,
    *,
    player_column: str,
    volume_expression: pl.Expr,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    labeled = deliveries.with_columns(
        pl.when(pl.col("match_format") == "T20I")
        .then(pl.lit("T20I"))
        .when(pl.col("competition_name").str.contains(r"(?i)\bIPL\b"))
        .then(pl.lit("IPL"))
        .otherwise(pl.lit("out_of_scope"))
        .alias("competition_type")
    )
    pressure = labeled.filter(pl.col("is_high_pressure")).with_columns(
        volume_expression.alias("_exposure_volume")
    )
    top_ids = leaderboard.select(
        "player_id",
        pl.col("player_name").alias("leaderboard_player_name"),
    )
    exposure = (
        pressure.group_by(
            pl.col(player_column).alias("player_id"),
            "competition_type",
            "innings",
        )
        .agg(pl.col("_exposure_volume").sum().alias("high_pressure_volume"))
        .join(top_ids, on="player_id", how="semi")
        .sort(
            [
                "competition_type",
                "innings",
                "high_pressure_volume",
                "player_id",
            ],
            descending=[False, False, True, False],
        )
    )
    summary = exposure.group_by(["competition_type", "innings"]).agg(
        pl.col("high_pressure_volume").sum().alias("top10_high_pressure_volume"),
        pl.col("player_id").n_unique().alias("represented_players"),
    ).sort(["competition_type", "innings"])
    return exposure, summary


def audit_rankings(
    deliveries: pl.DataFrame,
    batting_top10: pl.DataFrame,
    bowling_top10: pl.DataFrame,
    batting_eligible: pl.DataFrame,
    bowling_eligible: pl.DataFrame,
    batting_match_impacts: pl.DataFrame,
    bowling_match_impacts: pl.DataFrame,
) -> dict[str, object]:
    """Return all PRD ranking integrity and cross-split diagnostics."""
    validate_top10(batting_top10)
    validate_top10(bowling_top10)
    batting_exposure, batting_summary = _top10_exposure(
        deliveries,
        batting_top10,
        player_column="striker_id",
        volume_expression=(
            pl.col("extras_type").fill_null("").str.to_lowercase() != "wide"
        ).cast(pl.Int64),
    )
    bowling_exposure, bowling_summary = _top10_exposure(
        deliveries,
        bowling_top10,
        player_column="bowler_id",
        volume_expression=pl.col("legal_ball_event"),
    )
    batting_rho, batting_split_players = split_half_rank_stability(
        batting_match_impacts.filter(
            pl.col("player_id").is_in(
                batting_eligible.get_column("player_id").to_list()
            )
        ),
        deliveries,
        impact_column="match_net_impact",
        balls_column="high_pressure_balls_faced",
        scale=100,
    )
    bowling_rho, bowling_split_players = split_half_rank_stability(
        bowling_match_impacts.filter(
            pl.col("player_id").is_in(
                bowling_eligible.get_column("player_id").to_list()
            )
        ),
        deliveries,
        impact_column="match_runs_saved",
        balls_column="high_pressure_legal_balls",
        scale=6,
    )
    return {
        "batting_exposure": batting_exposure,
        "batting_exposure_summary": batting_summary,
        "bowling_exposure": bowling_exposure,
        "bowling_exposure_summary": bowling_summary,
        "batting_split_half_rho": batting_rho,
        "batting_split_half_players": batting_split_players,
        "bowling_split_half_rho": bowling_rho,
        "bowling_split_half_players": bowling_split_players,
        "passes_split_half_stability": (
            batting_rho >= MIN_SPLIT_HALF_RHO
            and bowling_rho >= MIN_SPLIT_HALF_RHO
        ),
        "eligible_batters": batting_eligible.height,
        "eligible_bowlers": bowling_eligible.height,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--allow-stability-failure",
        action="store_true",
        help="write audit artifacts and continue when split-half rho is below target",
    )
    args = parser.parse_args()
    result = audit_rankings(
        pl.read_parquet(args.input_dir / "normalized_deliveries.parquet"),
        pl.read_parquet(args.input_dir / "top10_batters.parquet"),
        pl.read_parquet(args.input_dir / "top10_bowlers.parquet"),
        pl.read_parquet(args.input_dir / "eligible_batters.parquet"),
        pl.read_parquet(args.input_dir / "eligible_bowlers.parquet"),
        pl.read_parquet(args.input_dir / "batting_match_impacts.parquet"),
        pl.read_parquet(args.input_dir / "bowling_match_impacts.parquet"),
    )
    print(
        f"batting split-half rho: {result['batting_split_half_rho']:.4f} "
        f"({result['batting_split_half_players']} players)"
    )
    print(
        f"bowling split-half rho: {result['bowling_split_half_rho']:.4f} "
        f"({result['bowling_split_half_players']} players)"
    )
    print("Batting Top-10 exposure:")
    print(result["batting_exposure_summary"])
    print("Bowling Top-10 exposure:")
    print(result["bowling_exposure_summary"])
    result["batting_exposure"].write_parquet(
        args.input_dir / "batting_top10_exposure.parquet"
    )
    result["bowling_exposure"].write_parquet(
        args.input_dir / "bowling_top10_exposure.parquet"
    )
    pl.DataFrame(
        [
            {
                "discipline": "batting",
                "split_half_rho": result["batting_split_half_rho"],
                "eligible_players": result["batting_split_half_players"],
                "target_rho": MIN_SPLIT_HALF_RHO,
                "meets_target": result["batting_split_half_rho"]
                >= MIN_SPLIT_HALF_RHO,
            },
            {
                "discipline": "bowling",
                "split_half_rho": result["bowling_split_half_rho"],
                "eligible_players": result["bowling_split_half_players"],
                "target_rho": MIN_SPLIT_HALF_RHO,
                "meets_target": result["bowling_split_half_rho"]
                >= MIN_SPLIT_HALF_RHO,
            },
        ]
    ).write_parquet(args.input_dir / "ranking_audit_summary.parquet")
    if not result["passes_split_half_stability"]:
        message = f"Split-half stability target rho >= {MIN_SPLIT_HALF_RHO:.2f} not met"
        if args.allow_stability_failure:
            print(f"WARNING: {message}; continuing by explicit request")
        else:
            raise SystemExit(message)


if __name__ == "__main__":
    main()
