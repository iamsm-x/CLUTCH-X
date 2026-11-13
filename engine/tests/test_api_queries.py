import duckdb

from clutch_x.api.queries import query_pressure_timeline
from clutch_x.api.schemas import AnalyticsFilters


def _create_deliveries(connection, rows: list[tuple[object, ...]]) -> None:
    connection.execute(
        "CREATE TABLE normalized_deliveries ("
        "competition_name VARCHAR, match_format VARCHAR, innings INTEGER, "
        "knock_out BOOLEAN, overid INTEGER, pressure_index DOUBLE, "
        "is_high_pressure BOOLEAN, is_wicket BOOLEAN)"
    )
    connection.executemany(
        "INSERT INTO normalized_deliveries VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def test_timeline_uses_parameterized_filters_and_ignores_selected_over() -> None:
    with duckdb.connect(":memory:") as connection:
        _create_deliveries(
            connection,
            [
                ("Indian Premier League (IPL)", "T20", 1, False, 1, 62.0, True, False),
                ("Indian Premier League (IPL)", "T20", 1, True, 2, 40.0, False, True),
                ("Indian Premier League (IPL)", "T20", 2, False, 1, 80.0, True, False),
                ("International T20", "T20I", 1, False, 1, 70.0, True, True),
            ],
        )
        result = query_pressure_timeline(
            connection,
            innings=1,
            filters=AnalyticsFilters(
                competition="IPL",
                match_stage="ALL",
                over=2,
            ),
        )

    assert result.get_column("over").to_list() == [1, 2]
    assert result.get_column("average_pressure_index").to_list() == [62.0, 40.0]
    assert result.get_column("high_pressure_deliveries").to_list() == [1, 0]


def test_timeline_stage_filter_excludes_non_knockout_matches() -> None:
    with duckdb.connect(":memory:") as connection:
        _create_deliveries(
            connection,
            [
                ("Indian Premier League (IPL)", "T20", 2, False, 18, 50.0, False, False),
                ("Indian Premier League (IPL)", "T20", 2, True, 18, 90.0, True, True),
            ],
        )
        result = query_pressure_timeline(
            connection,
            innings=2,
            filters=AnalyticsFilters(
                competition="IPL",
                match_stage="KNOCKOUTS_PLAYOFFS",
            ),
        )

    assert result.get_column("over").to_list() == [18]
    assert result.get_column("average_pressure_index").to_list() == [90.0]
