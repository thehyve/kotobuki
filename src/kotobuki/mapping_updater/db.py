from collections.abc import Sequence

from omop_cdm.regular.cdm54 import Concept, ConceptRelationship
from sqlalchemy import and_, func, select
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
        result = NewMap(concepts=target_concepts, map_path=path)
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


def find_all_homonyms(
    concept: Concept, case_insensitive: bool, session: Session
) -> Sequence[Concept]:
    """Get Concept ORM objects that match the concept_name."""
    if case_insensitive:
        homonyms = session.scalars(
            select(Concept).where(
                and_(
                    func.lower(Concept.concept_name) == concept.concept_name.lower(),
                    Concept.concept_id != concept.concept_id,
                )
            )
        ).all()
    else:
        homonyms = session.scalars(
            select(Concept).where(
                and_(
                    Concept.concept_name == concept.concept_name,
                    Concept.concept_id != concept.concept_id,
                )
            )
        ).all()
    return homonyms


def find_suitable_homonym(
    homonyms: Sequence[Concept], session: Session, concept: Concept
) -> NewMap | None:
    """
    Return a new mapping for a homonym that maps to a standard concept.

    If multiple homonyms map to a standard concept, those that are from
    the same domain as the original concept are prioritized. If there
    are no homonyms, or none map to a standard concept, return None.
    """
    start_path = [MapLink(concept)]
    mappings: list[NewMap] = []
    for h in homonyms:
        path = start_path.copy()
        path.append(MapLink(h, Relationship.HOMONYM))
        new_map = find_standard_concepts(h.concept_id, session, path)
        if new_map is not None:
            mappings.append(new_map)
    same_domain_mappings = [
        nm for nm in mappings if any(c.domain_id == concept.domain_id for c in nm.concepts)
    ]
    if same_domain_mappings:
        return same_domain_mappings[0]
    if mappings:
        return mappings[0]
    return None


def find_new_mapping(
    concept: Concept,
    search_homonyms: bool,
    ignore_case: bool,
    session: Session,
) -> NewMap | None:
    # Try to find standard concepts via concept relationships
    new_map = find_standard_concepts(concept.concept_id, session, [MapLink(concept)])
    # Alternatively via concepts with an identical name
    if search_homonyms and new_map is None:
        homonyms = find_all_homonyms(concept, ignore_case, session)
        new_map = find_suitable_homonym(homonyms, session, concept)
    return new_map
