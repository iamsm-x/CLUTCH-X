"""Source-file contracts for the uploaded CLUTCH-X data pack."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceContract:
    required_columns: tuple[str, ...]
    primary_key: tuple[str, ...]


SOURCE_CONTRACTS = {
    "ball_by_ball.csv": SourceContract(
        required_columns=(
            "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
            "batting_team_id", "bowling_team_id", "striker_id", "striker_name",
            "non_striker_id", "non_striker_name", "bowler_id", "bowler_name",
            "batting_order", "runs", "is_four", "is_six", "is_wicket",
            "dismissal_type_id", "dismissal_type", "dismissed_player_id",
            "extras_type", "extras1_runs", "extras_2_runs", "delivery_ist_time",
        ),
        primary_key=("match_id", "innings", "innings_ball_num"),
    ),
    "matches.csv": SourceContract(
        required_columns=(
            "match_id", "comp_id", "match_number", "match_date", "stage",
            "home_team_id", "home_team", "away_team_id", "away_team",
            "first_inn_revised_overs", "second_inn_revised_overs",
            "revised_target", "knock_out", "result",
        ),
        primary_key=("match_id",),
    ),
    "competitions.csv": SourceContract(
        required_columns=("comp_id", "comp_name", "match_format", "season"),
        primary_key=("comp_id",),
    ),
    "playing_eleven.csv": SourceContract(
        required_columns=(
            "match_id", "team_id", "player_id", "batting_order", "is_played",
            "is_captain", "is_wk", "is_impact", "is_impact_off",
        ),
        primary_key=("match_id", "team_id", "player_id", "batting_order"),
    ),
    "teams.csv": SourceContract(
        required_columns=("comp_id", "team_id", "team_name"),
        primary_key=("comp_id", "team_id"),
    ),
    "competition_team_player_mapping.csv": SourceContract(
        required_columns=(
            "comp_id", "comp_name", "team_id", "team_name", "player_id",
            "player_name",
        ),
        primary_key=("comp_id", "team_id", "player_id"),
    ),
}

INTEGER_COLUMNS = {
    "ball_by_ball.csv": (
        "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
        "batting_team_id", "bowling_team_id", "striker_id", "non_striker_id",
        "bowler_id", "batting_order", "runs", "dismissal_type_id",
        "dismissed_player_id", "extras1_runs", "extras_2_runs",
    ),
    "matches.csv": (
        "match_id", "comp_id", "match_number", "venue_id", "home_team_id",
        "away_team_id", "home_team_captain_id", "away_team_captain_id",
        "toss_win_team_id", "man_of_the_match", "first_inn_revised_overs",
        "second_inn_revised_overs", "revised_target", "win_team_id",
    ),
    "competitions.csv": ("comp_id",),
    "playing_eleven.csv": ("match_id", "team_id", "player_id", "batting_order"),
    "teams.csv": ("comp_id", "team_id"),
    "competition_team_player_mapping.csv": ("comp_id", "team_id", "player_id"),
}

BOOLEAN_COLUMNS = {
    "ball_by_ball.csv": ("is_four", "is_six", "is_wicket"),
    "matches.csv": ("knock_out",),
    "playing_eleven.csv": (
        "is_played", "is_captain", "is_wk", "is_impact", "is_impact_off",
    ),
}

NULLABLE_COLUMNS = {
    "ball_by_ball.csv": (
        "dismissal_type_id", "dismissal_type", "dismissed_player_id",
    ),
    "matches.csv": (
        "match_number", "venue_id", "home_team_id", "away_team_id",
        "home_team_captain_id", "away_team_captain_id", "toss_win_team_id",
        "toss_opted", "man_of_the_match", "first_inn_revised_overs",
        "second_inn_revised_overs", "revised_target", "win_team_id",
    ),
    "playing_eleven.csv": ("batting_order", "is_captain", "is_wk"),
}

DATA_FILES = tuple(SOURCE_CONTRACTS)
