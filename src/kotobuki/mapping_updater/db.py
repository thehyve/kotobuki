from collections.abc import Sequence

from omop_cdm.regular.cdm54 import Concept, ConceptRelationship
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .relationship import (
    VAL_TO_RELATIONSHIP,
    MapLink,
    NewMap,
    Relationship,
)


def query_concepts(concept_ids: set[int], session: Session) -> Sequence[Concept]:
    """Get Concept ORM objects for all given concept_ids."""
    return session.scalars(select(Concept).filter(Concept.concept_id.in_(concept_ids))).all()


def get_mappings(concept_id: int, session: Session) -> Sequence[ConceptRelationship]:
    """Get relationship mappings for a given concept_id."""
    return session.scalars(
        select(ConceptRelationship).filter(
            and_(
                ConceptRelationship.concept_id_1 == concept_id,
                ConceptRelationship.relationship_id.in_(Relationship.db_relationships()),
            )
        )
    ).all()


def find_maps_to_value_relationship(
    mappings: Sequence[ConceptRelationship],
) -> list[Concept]:
    return [m.concept_2 for m in mappings if m.relationship_id == Relationship.MAPS_TO_VALUE.value]


def find_standard_concepts(
    concept_id: int, session: Session, path: list[MapLink]
) -> NewMap | None:
    """Search recursively for a standard concept."""
    mappings = get_mappings(concept_id, session)
    maps_to_mappings = [m for m in mappings if m.relationship_id == Relationship.MAPS_TO.value]

    # If there is one (or more) Maps to relationship, we are done
    if maps_to_mappings:
        target_concepts = [c.concept_2 for c in maps_to_mappings]
        result = NewMap(concepts=target_concepts)
        for target_concept in target_concepts:
            path.append(MapLink(target_concept, via=Relationship.MAPS_TO))
        result.map_path = path
        result.value_as_concept = find_maps_to_value_relationship(mappings)
        return result

    for mapping in mappings:
        if mapping.relationship_id in {
            Relationship.REPLACED.value,
            Relationship.POSS_EQUIVALENT.value,
            Relationship.SAME_AS.value,
        }:
            new_path = path.copy()
            via = VAL_TO_RELATIONSHIP[mapping.relationship_id]
            new_path.append(MapLink(mapping.concept_2, via))
            return find_standard_concepts(mapping.concept_id_2, session, new_path)
    return None


def find_all_homonyms(concept_name: str, session: Session) -> Sequence[Concept]:
    """Get Concept ORM objects that match the concept_name."""
    return session.scalars(select(Concept).where(Concept.concept_name == concept_name)).all()


def find_suitable_homonym(
    homonyms: Sequence[Concept], session: Session, concept: Concept
) -> NewMap | None:
    """Return first homonym concept that maps to a standard concept."""
    start_path = [MapLink(concept)]
    for h in homonyms:
        path = start_path.copy()
        path.append(MapLink(h, Relationship.HOMONYM))
        new_map = find_standard_concepts(h.concept_id, session, path)
        if new_map is not None:
            return new_map
    return None


def find_new_mapping(concept: Concept, search_homonyms: bool, session: Session) -> NewMap | None:
    # Try to find standard concepts via concept relationships
    new_map = find_standard_concepts(concept.concept_id, session, [MapLink(concept)])
    # Alternatively via concepts with an identical name
    if search_homonyms and new_map is None:
        homonyms = find_all_homonyms(concept.concept_name, session)
        new_map = find_suitable_homonym(homonyms, session, concept)
    return new_map
