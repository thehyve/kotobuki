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
        s = f"{self.concept.concept_id} {self.concept.concept_name}"
        if self.via is not None:
            s = f"[{self.via.value}] {s}"
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

    def to_map_path_data(self) -> dict[str, dict[str, list[str]]]:
        """Convert to dict suitable for writing to mapping path file."""
        if not self.map_path:
            return {}
        # we only want to show the intermediate steps in the mapping
        # path, so we ignore the source concept and the final target
        map_path = [str(ml) for ml in self.map_path[1:-1]]
        map_properties = {
            "map_path": map_path,
            "maps_to": [f"{c.concept_id} {c.concept_name}" for c in self.concepts],
            "maps_to_value": [f"{c.concept_id} {c.concept_name}" for c in self.value_as_concept],
        }
        # Remove keys that point to empty lists
        map_properties = {k: v for k, v in map_properties.items() if v}

        original_concept = self.map_path[0].concept
        return {
            f"{original_concept.concept_id} {original_concept.concept_name}": map_properties,
        }

    def render_map_path(self) -> str:
        return " ".join([str(ml) for ml in self.map_path])
