import csv
from pathlib import Path

import polars as pl
import pytest

from clutch_x.etl.clean_matches import clean_deliveries
from clutch_x.etl.load_sources import load_sources
from clutch_x.etl.schemas import INTEGER_COLUMNS, SOURCE_CONTRACTS
from clutch_x.etl.validate_sources import DatasetValidationError, validate_data_dir


def _write_valid_data_pack(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rows = {
        "ball_by_ball.csv": {
            "match_id": "1", "innings": "1", "overid": "1", "over_ball_num": "1",
            "innings_ball_num": "1", "batting_team_id": "10", "bowling_team_id": "11",
            "striker_id": "20", "striker_name": "Batter", "non_striker_id": "21",
            "non_striker_name": "Partner", "bowler_id": "30", "bowler_name": "Bowler",
            "batting_order": "1", "runs": "0", "is_four": "false", "is_six": "false",
            "is_wicket": "false", "dismissal_type_id": "", "dismissal_type": "",
            "dismissed_player_id": "", "extras_type": "None", "extras1_runs": "0",
            "extras_2_runs": "0", "delivery_ist_time": "2022-01-01 00:00:00 UTC",
        },
        "matches.csv": {
            "match_id": "1", "comp_id": "100", "match_number": "1",
            "match_date": "2022-01-01", "stage": "League", "home_team_id": "10",
            "home_team": "Home", "away_team_id": "11", "away_team": "Away",
            "first_inn_revised_overs": "", "second_inn_revised_overs": "",
            "revised_target": "", "knock_out": "0", "result": "Home won",
        },
        "competitions.csv": {
            "comp_id": "100", "comp_name": "IPL 2022", "match_format": "T20",
            "season": "2022",
        },
        "playing_eleven.csv": {
            "match_id": "1", "team_id": "10", "player_id": "20",
            "batting_order": "1", "is_played": "true", "is_captain": "false",
            "is_wk": "false", "is_impact": "0", "is_impact_off": "0",
        },
        "teams.csv": {"comp_id": "100", "team_id": "10", "team_name": "Home"},
        "competition_team_player_mapping.csv": {
            "comp_id": "100", "comp_name": "IPL 2022", "team_id": "10",
            "team_name": "Home", "player_id": "20", "player_name": "Batter",
        },
    }

    for filename, contract in SOURCE_CONTRACTS.items():
        row = rows[filename]
        for column in contract.required_columns:
            if column not in row:
                row[column] = "0" if column in INTEGER_COLUMNS.get(filename, ()) else "sample"
        with (directory / filename).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=contract.required_columns)
            writer.writeheader()
            writer.writerow(row)


def test_validate_data_pack_contracts_and_relationships(tmp_path: Path) -> None:
    _write_valid_data_pack(tmp_path)

    counts = validate_data_dir(tmp_path)

    assert counts["ball_by_ball.csv"] == 1
    assert counts["matches.csv"] == 1


def test_validate_rejects_broken_match_reference(tmp_path: Path) -> None:
    _write_valid_data_pack(tmp_path)
    path = tmp_path / "ball_by_ball.csv"
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
        headers = rows[0].keys()
    rows[0]["match_id"] = "999"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(DatasetValidationError, match="do not reference a known record"):
        validate_data_dir(tmp_path)


def test_load_sources_normalizes_numeric_and_boolean_columns(tmp_path: Path) -> None:
    _write_valid_data_pack(tmp_path)

    frames = load_sources(tmp_path)

    assert frames["ball_by_ball"].schema["runs"] == pl.Int64
    assert frames["ball_by_ball"].schema["is_wicket"] == pl.Boolean
    assert frames["playing_eleven"].schema["is_impact"] == pl.Boolean
    assert frames["playing_eleven"].get_column("is_impact").to_list() == [False]


def test_cleaning_excludes_super_overs_and_only_short_abandonments() -> None:
    match_three_balls = 30
    deliveries = pl.DataFrame(
        {
            "match_id": [1, 1, 2, 2] + [3] * match_three_balls + [4],
            "innings": [1, 3, 1, 1] + [1] * match_three_balls + [1],
            "extras_type": ["None", "None", "wide", "wide"]
            + ["None"] * match_three_balls
            + ["None"],
            "innings_ball_num": [1, 1, 1, 2]
            + list(range(1, match_three_balls + 1))
            + [1],
        }
    )
    matches = pl.DataFrame(
        {
            "match_id": [1, 2, 3, 4],
            "comp_id": [1, 1, 1, 2],
            "result": ["Won", "Match Abandoned", "No Result", "Won"],
        }
    )
    competitions = pl.DataFrame(
        {
            "comp_id": [1, 2],
            "comp_name": ["International T20I", "Emerging Teams Asia Cup"],
            "match_format": ["T20I", "T20"],
        }
    )
    frames = {
        "ball_by_ball": deliveries,
        "matches": matches,
        "competitions": competitions,
    }

    cleaned, counts = clean_deliveries(frames)

    assert counts == {
        "input_deliveries": 35,
        "excluded_out_of_scope_deliveries": 1,
        "excluded_super_over_deliveries": 1,
        "excluded_insufficient_play_deliveries": 2,
        "output_deliveries": 31,
    }
    assert cleaned.group_by("match_id").len().sort("match_id").rows() == [
        (1, 1),
        (3, 30),
    ]
