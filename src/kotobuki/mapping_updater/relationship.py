from dataclasses import dataclass, field
from enum import Enum

from omop_cdm.regular.cdm54 import Concept


class Relationship(Enum):
    MAPS_TO = "Maps to"
    REPLACED = "Concept replaced by"
    POSS_EQUIVALENT = "Concept poss_eq to"
    SAME_AS = "Concept same_as to"
    MAPS_TO_VALUE = "Maps to value"
    HOMONYM = "Homonym"  # Same concept name (no direct vocabulary link)

    @staticmethod
    def db_relationships() -> set[str]:
        return {
            Relationship.MAPS_TO.value,
            Relationship.REPLACED.value,
            Relationship.POSS_EQUIVALENT.value,
            Relationship.SAME_AS.value,
            Relationship.MAPS_TO_VALUE.value,
        }


# Reverse lookup: enum string to enum
VAL_TO_RELATIONSHIP = {e.value: e for e in Relationship}


@dataclass
class MapLink:
    concept: Concept
    via: Relationship | None = None

    def __str__(self) -> str:
        s = f"[{self.concept.concept_id}] {self.concept.concept_name}"
        if self.via is not None:
            s = f"➡️ <{self.via.value}> {s}"
        return s


@dataclass
class NewMap:
    concepts: list[Concept]
    value_as_concept: list[Concept] = field(default_factory=list)
    map_path: list[MapLink] = field(default_factory=list)

    def __repr__(self):
        s = f"Maps to: {','.join(str(c.concept_id) for c in self.concepts)}"
        if self.value_as_concept:
            s = f"{s}\nMaps to value: {','.join(str(c.concept_id) for c in self.value_as_concept)}"
        return s

    def render_map_path(self) -> str:
        return " ".join([str(ml) for ml in self.map_path])
