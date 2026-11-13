import polars as pl

from clutch_x.etl.enrich_deliveries import attach_pre_delivery_state


def test_reconstructs_pre_delivery_totals_resources_and_chase_target() -> None:
    deliveries = pl.DataFrame(
        {
            "match_id": [1, 1, 1, 1, 1, 1],
            "innings": [1, 1, 1, 1, 2, 2],
            "innings_ball_num": [1, 2, 3, 4, 1, 2],
            "overid": [1, 1, 1, 1, 1, 1],
            "over_ball_num": [1, 2, 3, 4, 1, 2],
            "extras_type": ["None", "other", "None", "None", "None", "None"],
            "runs": [1, 0, 0, 4, 2, 2],
            "extras1_runs": [0, 1, 0, 0, 0, 0],
            "extras_2_runs": [0, 0, 0, 0, 0, 0],
            "is_wicket": [False, False, True, False, False, False],
            "first_inn_revised_overs": [6] * 6,
            "second_inn_revised_overs": [5] * 6,
            "revised_target": [4] * 6,
        }
    )

    states = attach_pre_delivery_state(deliveries)

    assert states.select(
        "innings",
        "pre_delivery_runs",
        "pre_delivery_wickets",
        "pre_delivery_legal_balls",
        "balls_remaining",
        "target",
        "runs_required",
    ).rows() == [
        (1, 0, 0, 0, 6, None, None),
        (1, 1, 0, 1, 5, None, None),
        (1, 2, 0, 1, 5, None, None),
        (1, 2, 1, 2, 4, None, None),
        (2, 0, 0, 0, 5, 4, 4),
        (2, 2, 0, 1, 4, 4, 2),
    ]
