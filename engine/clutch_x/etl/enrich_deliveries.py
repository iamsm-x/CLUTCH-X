"""Attach competition, match, team, and player metadata to deliveries."""

import polars as pl

from clutch_x.etl.delivery_rules import is_legal_delivery


def enrich_deliveries(frames: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Enrich delivery rows while preserving a one-row-per-delivery grain."""
    deliveries = frames["ball_by_ball"]
    match_metadata = frames["matches"].join(
        frames["competitions"].select(
            "comp_id",
            pl.col("comp_name").alias("competition_name"),
            "match_format",
            "season",
        ),
        on="comp_id",
        how="left",
        validate="m:1",
    )
    match_columns = [
        "match_id", "comp_id", "competition_name", "match_format", "season",
        "match_date", "stage", "knock_out", "first_inn_revised_overs",
        "second_inn_revised_overs", "revised_target", "result",
    ]
    enriched = deliveries.join(
        match_metadata.select(match_columns),
        on="match_id",
        how="left",
        validate="m:1",
    )

    teams = frames["teams"]
    batting_teams = teams.select(
        "comp_id",
        pl.col("team_id").alias("batting_team_id"),
        pl.col("team_name").alias("batting_team_name"),
    )
    bowling_teams = teams.select(
        "comp_id",
        pl.col("team_id").alias("bowling_team_id"),
        pl.col("team_name").alias("bowling_team_name"),
    )
    enriched = enriched.join(
        batting_teams,
        on=["comp_id", "batting_team_id"],
        how="left",
        validate="m:1",
    ).join(
        bowling_teams,
        on=["comp_id", "bowling_team_id"],
        how="left",
        validate="m:1",
    )

    players = frames["competition_team_player_mapping"]
    batter_mapping = players.select(
        "comp_id",
        pl.col("team_id").alias("batting_team_id"),
        pl.col("player_id").alias("striker_id"),
        pl.col("player_name").alias("mapped_striker_name"),
    )
    bowler_mapping = players.select(
        "comp_id",
        pl.col("team_id").alias("bowling_team_id"),
        pl.col("player_id").alias("bowler_id"),
        pl.col("player_name").alias("mapped_bowler_name"),
    )
    enriched = enriched.join(
        batter_mapping,
        on=["comp_id", "batting_team_id", "striker_id"],
        how="left",
        validate="m:1",
    ).join(
        bowler_mapping,
        on=["comp_id", "bowling_team_id", "bowler_id"],
        how="left",
        validate="m:1",
    )

    if enriched.height != deliveries.height:
        raise ValueError(
            "Metadata joins changed delivery row count: "
            f"{deliveries.height} input rows, {enriched.height} output rows"
        )
    return enriched.sort(["match_id", "innings", "innings_ball_num"])


def attach_pre_delivery_state(enriched: pl.DataFrame) -> pl.DataFrame:
    """Reconstruct score, wickets, target, and resources before each ball."""
    keys = ["match_id", "innings"]
    is_legal = is_legal_delivery()
    enriched = enriched.sort(["match_id", "innings", "innings_ball_num"]).with_columns(
        (pl.col("runs").fill_null(0)
         + pl.col("extras1_runs").fill_null(0)
         + pl.col("extras_2_runs").fill_null(0)).alias("delivery_total_runs"),
        pl.col("is_wicket").fill_null(False).cast(pl.Int64).alias("wicket_event"),
        is_legal.cast(pl.Int64).alias("legal_ball_event"),
    )
    first_innings_totals = (
        enriched.filter(pl.col("innings") == 1)
        .group_by("match_id")
        .agg(pl.col("delivery_total_runs").sum().alias("first_innings_total_runs"))
    )
    enriched = enriched.join(
        first_innings_totals,
        on="match_id",
        how="left",
        validate="m:1",
    ).with_columns(
        (pl.col("delivery_total_runs").cum_sum().over(keys)
         - pl.col("delivery_total_runs")).alias("pre_delivery_runs"),
        (pl.col("wicket_event").cum_sum().over(keys)
         - pl.col("wicket_event")).alias("pre_delivery_wickets"),
        (pl.col("legal_ball_event").cum_sum().over(keys)
         - pl.col("legal_ball_event")).alias("pre_delivery_legal_balls"),
        pl.when(pl.col("innings") == 1)
        .then(pl.col("first_inn_revised_overs").fill_null(120))
        .otherwise(pl.col("second_inn_revised_overs").fill_null(120))
        .alias("scheduled_legal_balls"),
        pl.when(
            (pl.col("innings") == 2)
            & pl.col("revised_target").is_not_null()
            & (pl.col("revised_target") > 0)
        )
        .then(pl.col("revised_target"))
        .when(pl.col("innings") == 2)
        .then(pl.col("first_innings_total_runs") + 1)
        .otherwise(None)
        .alias("target"),
    ).with_columns(
        pl.when(pl.col("innings") == 2)
        .then(pl.col("target") - pl.col("pre_delivery_runs"))
        .otherwise(None)
        .alias("runs_required"),
        (pl.col("scheduled_legal_balls") - pl.col("pre_delivery_legal_balls"))
        .clip(lower_bound=0)
        .alias("balls_remaining"),
        ((pl.col("overid") - 1) * 6 + pl.col("over_ball_num") - 1)
        .alias("delivery_sequence_ball"),
        pl.when(pl.col("overid") <= 6)
        .then(pl.lit("powerplay"))
        .when(pl.col("overid") <= 15)
        .then(pl.lit("middle"))
        .otherwise(pl.lit("death"))
        .alias("over_phase"),
    )
    return enriched


def build_delivery_states(frames: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build the enriched, pre-delivery-state dataset for valid innings."""
    enriched = enrich_deliveries(frames)
    return attach_pre_delivery_state(enriched).filter(pl.col("innings") <= 2)
