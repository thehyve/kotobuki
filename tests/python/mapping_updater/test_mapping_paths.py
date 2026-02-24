from omop_cdm.regular.cdm54 import Concept

from kotobuki.mapping_updater.relationship import MapLink, NewMap, Relationship

TARGET_CONCEPT1 = Concept(concept_id=3, concept_name="The golden standard")
TARGET_CONCEPT2 = Concept(concept_id=30, concept_name="The other golden standard")
SOURCE_CONCEPT1 = Concept(concept_id=2, concept_name="The golden non-standard")
HOMONYM_CONCEPT1 = Concept(concept_id=99, concept_name="THE GOLDEN NON-STANDARD")


def test_simple_mapping_path():
    map_links = [
        MapLink(concept=SOURCE_CONCEPT1),
        MapLink(concept=TARGET_CONCEPT1, via=Relationship.MAPS_TO),
    ]
    new_map = NewMap(concepts=[TARGET_CONCEPT1], map_path=map_links)
    map_path_data = new_map.to_map_path_data()
    assert map_path_data == {
        "2 The golden non-standard": {
            "maps_to": ["3 The golden standard"],
        }
    }


def test_via_homonym_mapping_path():
    map_links = [
        MapLink(concept=SOURCE_CONCEPT1),
        MapLink(concept=HOMONYM_CONCEPT1, via=Relationship.HOMONYM),
        MapLink(concept=TARGET_CONCEPT1, via=Relationship.MAPS_TO),
    ]
    new_map = NewMap(concepts=[TARGET_CONCEPT1], map_path=map_links)
    map_path_data = new_map.to_map_path_data()
    assert map_path_data == {
        "2 The golden non-standard": {
            "map_path": ["[Homonym] 99 THE GOLDEN NON-STANDARD"],
            "maps_to": ["3 The golden standard"],
        }
    }


# def test_one_to_two_mapping_path():
#     map_links= [
#         MapLink(concept=SOURCE_CONCEPT1),
#         MapLink(concept=TARGET_CONCEPT1, via=Relationship.MAPS_TO),
#     ]
#     new_map = NewMap(concepts=[TARGET_CONCEPT1], map_path=map_links)
#     map_path_data = new_map.to_map_path_data()
#     assert map_path_data == {
#         "2 The golden non-standard": {
#             "map_path": ["[Homonym] 99 THE GOLDEN NON-STANDARD"],
#             "maps_to": ["3 The golden standard"],
#         }
#     }

#
# def test_write_map_paths(tmp_path: Path, pg_db_engine: Engine):
#     tmp_usagi_file = write_tmp_usagi_file(tmp_path, USAGI_STCM_FILE)
#     update_usagi_file(pg_db_engine, "vocab", tmp_usagi_file, write_map_paths=True)
#     map_paths_file = next(tmp_path.glob("*.txt"))
#     with map_paths_file.open("r", encoding="utf8") as f:
#         lines = {line.strip() for line in f}
#     expected_lines = {
#         "[2] x depricated2 ➡️ <Maps to> [3] x standard",
#         "[1] x depricated1 ➡️ <Concept replaced by> [2] x depricated2 ➡️ <Maps to> [3] x standard",
#         "[7] History of halitosis ➡️ <Maps to> [8] History of",
#         "[10] one_to_two_map ➡️ <Maps to> [11] 1/2 ➡️ <Maps to> [12] 2/2",
#         "[13] dep_concept_two_values ➡️ <Maps to> [14] superstandard",
#     }
#     assert expected_lines == lines
