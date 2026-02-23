import pytest
from omop_cdm.regular.cdm54 import Concept
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from kotobuki.mapping_updater.db import find_new_mapping
from kotobuki.mapping_updater.relationship import NewMap

pytestmark = pytest.mark.usefixtures("create_vocab_tables")


def get_concept_by_id(session: Session, concept_id: int) -> Concept | None:
    return session.scalars(select(Concept).filter(Concept.concept_id == concept_id)).one_or_none()


def get_new_map(
    concept_id: int,
    engine: Engine,
    homonyms: bool = False,
    ignore_case: bool = False,
) -> NewMap | None:
    with Session(engine, expire_on_commit=False) as session, session.begin():
        concept = get_concept_by_id(session, concept_id=concept_id)
        return find_new_mapping(
            concept=concept,
            search_homonyms=homonyms,
            ignore_case=ignore_case,
            session=session,
        )


def test_no_map(pg_db_engine: Engine):
    """Concept with no relationships cannot be updated."""
    result = get_new_map(concept_id=4, engine=pg_db_engine)
    assert result is None


def test_simple_maps_to_standard(pg_db_engine: Engine):
    """Concept 2 maps to concept 3 directly (Maps to)."""
    result = get_new_map(concept_id=2, engine=pg_db_engine)
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 3
    assert not result.value_as_concept


def test_two_step_mapping(pg_db_engine: Engine):
    """Concept 1 is replaced by 2 and then maps to 3."""
    result = get_new_map(concept_id=1, engine=pg_db_engine)
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 3
    assert not result.value_as_concept


def test_homonym_mapping_inactive(pg_db_engine: Engine):
    """Concept 5 can only map to 6 via a homonym."""
    result = get_new_map(concept_id=5, engine=pg_db_engine, homonyms=False)
    # Without activating homonym search, no mapping should be found
    assert result is None


def test_homonym_mapping_active(pg_db_engine: Engine):
    """Concept 5 can only map to 6 via a homonym."""
    result = get_new_map(concept_id=5, engine=pg_db_engine, homonyms=True)
    # With activated homonym search, it should map to 6
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 6
    assert not result.value_as_concept


def test_maps_to_value(pg_db_engine: Engine):
    """Concept 7 has both maps to and maps to value relationships."""
    result = get_new_map(concept_id=7, engine=pg_db_engine)
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 8
    assert len(result.value_as_concept) == 1
    assert result.value_as_concept[0].concept_id == 9


def test_one_maps_to_two(pg_db_engine: Engine):
    """Concept 10 has maps to relationships to 11 and 12."""
    result = get_new_map(concept_id=10, engine=pg_db_engine)
    assert len(result.concepts) == 2
    assert {c.concept_id for c in result.concepts} == {11, 12}
    assert not result.value_as_concept


def test_multiple_maps_to_value(pg_db_engine: Engine):
    """Concept 13 has maps to value relationships to 15 and 16."""
    result = get_new_map(concept_id=13, engine=pg_db_engine)
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 14
    assert {c.concept_id for c in result.value_as_concept} == {15, 16}
