import csv
import filecmp
import shutil
from pathlib import Path

import pytest
from sqlalchemy import Engine

from kotobuki import update_usagi_file

pytestmark = pytest.mark.usefixtures("create_vocab_tables")


_DIR = Path(__file__)
TEST_DATA_DIR = _DIR.parent / "test_data"
USAGI_DIR = TEST_DATA_DIR / "usagi_files"
USAGI_STCM_FILE = USAGI_DIR / "stcm" / "usagi_test_stcm.csv"


def write_tmp_usagi_file(tmp_path: Path, original_usagi_file: Path) -> Path:
    tmp_usagi_file = tmp_path / original_usagi_file.name
    shutil.copyfile(original_usagi_file, tmp_usagi_file)
    return tmp_usagi_file


def test_inspect_only_does_not_change_file(tmp_path: Path, pg_db_engine: Engine):
    tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
    assert len(list(tmp_path.glob("*"))) == 1
    update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, inspect_only=True)
    assert len(list(tmp_path.glob("*"))) == 1
    assert filecmp.cmp(USAGI_STCM_FILE, tmp_usagi_file)


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


def test_overwrite(tmp_path: Path, pg_db_engine: Engine):
    tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
    update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, overwrite=True)
    with tmp_usagi_file.open("r", encoding="utf8") as f:
        reader = csv.DictReader(f)
        mappings = [(line["source_code"], line["target_concept_id"]) for line in reader]
    assert mappings == [
        ("X1", "3"),
        ("X2", "3"),
        ("X3", "3"),
        ("X4", "4"),
        ("X5", "5"),
        ("X6", "6"),
        ("X7", "8"),
        ("X7", "9"),
        ("X8", "8"),
        ("X9", "9"),
        ("X10", "11"),
        ("X10", "12"),
        ("X11", "11"),
        ("X12", "12"),
        ("X13", "14"),
        ("X13", "15"),
        ("X13", "16"),
        ("X14", "14"),
        ("X15", "15"),
        ("X16", "16"),
    ]


def test_homonyms(tmp_path: Path, pg_db_engine: Engine):
    tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
    update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, overwrite=True, allow_homonyms=True)
    with tmp_usagi_file.open("r", encoding="utf8") as f:
        reader = csv.DictReader(f)
        mappings = [(line["source_code"], line["target_concept_id"]) for line in reader]
    assert mappings == [
        ("X1", "3"),
        ("X2", "3"),
        ("X3", "3"),
        ("X4", "4"),
        ("X5", "6"),  # Now mapped to 6 via a homonym
        ("X6", "6"),
        ("X7", "8"),
        ("X7", "9"),
        ("X8", "8"),
        ("X9", "9"),
        ("X10", "11"),
        ("X10", "12"),
        ("X11", "11"),
        ("X12", "12"),
        ("X13", "14"),
        ("X13", "15"),
        ("X13", "16"),
        ("X14", "14"),
        ("X15", "15"),
        ("X16", "16"),
    ]
