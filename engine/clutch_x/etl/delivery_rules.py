"""Shared ball-legality rules for source-specific extras labels."""

import polars as pl

ILLEGAL_DELIVERY_TYPES = ("wide", "overstep", "other")
NON_BOWLER_CHARGED_EXTRAS = ("byes", "legbyes", "penalty")
BOWLER_CREDITED_DISMISSALS = (
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stump",
    "hit wicket",
)


def is_legal_delivery() -> pl.Expr:
    """Return whether a source delivery counts as a legal ball."""
    return ~pl.col("extras_type").fill_null("").str.to_lowercase().is_in(
        ILLEGAL_DELIVERY_TYPES
    )


def bowler_runs_conceded() -> pl.Expr:
    """Return delivery runs charged to the bowler under the source convention."""
    is_non_bowler_charged = pl.col("extras_type").fill_null("").str.to_lowercase().is_in(
        NON_BOWLER_CHARGED_EXTRAS
    )
    return (
        pl.when(is_non_bowler_charged)
        .then(
            pl.col("delivery_total_runs")
            - pl.col("extras1_runs").fill_null(0)
            - pl.col("extras_2_runs").fill_null(0)
        )
        .otherwise(pl.col("delivery_total_runs"))
    )
