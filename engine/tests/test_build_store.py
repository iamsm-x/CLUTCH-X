import duckdb
import polars as pl

from clutch_x.etl.build_store import build_analytical_store
from clutch_x.etl.schemas import DATA_FILES


def test_build_store_materializes_parquet_and_records_provenance(tmp_path) -> None:
    processed_dir = tmp_path / "processed"
    data_dir = tmp_path / "source"
    processed_dir.mkdir()
    data_dir.mkdir()
    pl.DataFrame({"player_id": [7, 8], "score": [91.0, 87.0]}).write_parquet(
        processed_dir / "top10_batters.parquet"
    )
    for file_name in DATA_FILES:
        (data_dir / file_name).write_text(file_name, encoding="utf-8")
    store_path = tmp_path / "store" / "clutch_x.duckdb"

    artifacts = build_analytical_store(processed_dir, store_path, data_dir)

    assert artifacts == [("top10_batters", "top10_batters.parquet", 2)]
    with duckdb.connect(str(store_path), read_only=True) as connection:
        assert connection.execute(
            "SELECT player_id FROM top10_batters ORDER BY player_id"
        ).fetchall() == [(7,), (8,)]
        assert connection.execute("SELECT COUNT(*) FROM source_manifest").fetchone()[0] == len(
            DATA_FILES
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM configuration_manifest"
        ).fetchone()[0] > 0
        assert connection.execute(
            "SELECT value FROM artifact_metadata WHERE key = 'store_schema_version'"
        ).fetchone()[0] == "1"
