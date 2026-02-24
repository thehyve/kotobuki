from pathlib import Path

import pytest
from omop_cdm.regular.cdm54 import Concept
from sqlalchemy import Engine

from kotobuki.mapping_updater.relationship import MapLink, NewMap, Relationship
from kotobuki.mapping_updater.update_usagi import update_usagi_file
from tests.python.mapping_updater.conftest import (
    USAGI_STCM_FILE,
    read_yaml_file,
    write_tmp_usagi_file,
)

TARGET_CONCEPT1 = Concept(concept_id=3, concept_name="The gold standard")
TARGET_CONCEPT2 = Concept(concept_id=30, concept_name="The other gold standard")
VALUE_CONCEPT1 = Concept(concept_id=40, concept_name="The gold value")
SOURCE_CONCEPT1 = Concept(concept_id=2, concept_name="The gold non-standard")
HOMONYM_CONCEPT1 = Concept(concept_id=99, concept_name="THE GOLD NON-STANDARD")


def test_simple_mapping_path():
    map_links = [MapLink(concept=SOURCE_CONCEPT1)]
    new_map = NewMap(concepts=[TARGET_CONCEPT1], map_path=map_links)
    assert new_map.to_map_path_data() == {
        "2 The gold non-standard": {
            "maps_to": ["3 The gold standard"],
        }
    }


def test_via_homonym_mapping_path():
    map_links = [
        MapLink(concept=SOURCE_CONCEPT1),
        MapLink(concept=HOMONYM_CONCEPT1, via=Relationship.HOMONYM),
    ]
    new_map = NewMap(concepts=[TARGET_CONCEPT1], map_path=map_links)
    assert new_map.to_map_path_data() == {
        "2 The gold non-standard": {
            "map_path": ["(Homonym) 99 THE GOLD NON-STANDARD"],
            "maps_to": ["3 The gold standard"],
        }
    }


def test_one_to_two_mapping_path():
    map_links = [MapLink(concept=SOURCE_CONCEPT1)]
    new_map = NewMap(concepts=[TARGET_CONCEPT1, TARGET_CONCEPT2], map_path=map_links)
    assert new_map.to_map_path_data() == {
        "2 The gold non-standard": {
            "maps_to": ["3 The gold standard", "30 The other gold standard"],
        }
    }


def test_maps_to_value_mapping_path():
    map_links = [MapLink(concept=SOURCE_CONCEPT1)]
    new_map = NewMap(
        concepts=[TARGET_CONCEPT1],
        value_as_concept=[VALUE_CONCEPT1],
        map_path=map_links,
    )
    assert new_map.to_map_path_data() == {
        "2 The gold non-standard": {
            "maps_to": ["3 The gold standard"],
            "maps_to_value": ["40 The gold value"],
        }
    }


@pytest.mark.usefixtures("create_vocab_tables")
def test_write_map_paths_e2e(tmp_path: Path, pg_db_engine: Engine):
    tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
    update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, write_map_paths=True)
    map_paths_file = next(tmp_path.glob("*.yml"))
    contents = read_yaml_file(map_paths_file)
    expected_contents = {
        "1 x deprecated1": {
            "map_path": ["(Concept replaced by) 2 x deprecated2"],
            "maps_to": ["3 x standard"],
        },
        "2 x deprecated2": {"maps_to": ["3 x standard"]},
        "7 History of halitosis": {"maps_to": ["8 History of"], "maps_to_value": ["9 Halitosis"]},
        "10 one_to_two_map": {"maps_to": ["11 1/2", "12 2/2"]},
        "13 dep_concept_two_values": {
            "maps_to": ["14 superstandard"],
            "maps_to_value": ["15 val1", "16 val2"],
        },
    }
    assert expected_contents == contents
