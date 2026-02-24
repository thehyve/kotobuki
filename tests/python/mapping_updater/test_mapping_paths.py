from pathlib import Path

from sqlalchemy import Engine

from kotobuki import update_usagi_file
from tests.python.mapping_updater.conftest import USAGI_STCM_FILE, write_tmp_usagi_file


def test_write_map_paths(tmp_path: Path, pg_db_engine: Engine):
    tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
    update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, write_map_paths=True)
    map_paths_file = next(tmp_path.glob("*.txt"))
    with map_paths_file.open("r", encoding="utf8") as f:
        lines = {line.strip() for line in f}
    expected_lines = {
        "[2] x depricated2 ➡️ <Maps to> [3] x standard",
        "[1] x depricated1 ➡️ <Concept replaced by> [2] x depricated2 ➡️ <Maps to> [3] x standard",
        "[7] History of halitosis ➡️ <Maps to> [8] History of",
        "[10] one_to_two_map ➡️ <Maps to> [11] 1/2 ➡️ <Maps to> [12] 2/2",
        "[13] dep_concept_two_values ➡️ <Maps to> [14] superstandard",
    }
    assert expected_lines == lines
