import pytest
from sqlalchemy import Engine

from tests.python.mapping_updater.test_usagi_mappings import get_new_map

pytestmark = pytest.mark.usefixtures("create_vocab_tables")


def test_find_standard_concept_via_case_insensitive_homonym(pg_db_engine: Engine):
    """
    The concept QzErTy is non-standard without a relationship to a standard concept,
    however, there is the standard homonym "qzerty". Test if this homonym is picked up correctly.
    """
    result = get_new_map(
        concept_id=19,
        engine=pg_db_engine,
        homonyms=True,
        ignore_case=True,
    )
    assert len(result.concepts) == 1
    assert result.concepts[0].concept_id == 20
    assert not result.value_as_concept


def test_NOT_find_standard_concept_via_case_insensitive_homonym(pg_db_engine: Engine):
    """
    Test if "qzerty" is not picked up from "QzErTy" when ignore_case is False.
    """
    result = get_new_map(
        concept_id=19,
        engine=pg_db_engine,
        homonyms=True,
        ignore_case=False,
    )
    assert result is None
