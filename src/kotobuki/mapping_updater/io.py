import csv
import logging
from collections.abc import Collection
from pathlib import Path
from time import strftime, time
from typing import Any

import pandas as pd
import yaml
from omop_cdm.regular.cdm54 import Concept

from .relationship import NewMap

logger = logging.getLogger(__name__)


CONCEPT_ID_COLUMNS = {
    "conceptId",  # Usagi save file
    "targetConceptId",  # Usagi review file
    "target_concept_id",  # STCM file
}

USAGI_DATE_FORMAT = "%Y%m%d"


def _get_concept_col(header: pd.Index) -> str:
    for col in CONCEPT_ID_COLUMNS:
        if col in header:
            return col
    raise ValueError(
        f"Could not find column containing concept_id values. "
        f"Allowed columns: {CONCEPT_ID_COLUMNS}"
    )


def get_target_concepts(usagi_file: Path) -> set[int]:
    """Get set of target concept_ids from an Usagi file."""
    concept_col = _get_concept_col(pd.read_csv(usagi_file, nrows=0).columns)
    df = pd.read_csv(usagi_file, usecols=[concept_col], dtype="Int32", index_col=False)
    df.dropna(inplace=True)
    concept_ids = set(df[concept_col].unique())
    # convert numpy int32 to regular python int
    concept_ids = {n.item() for n in concept_ids}
    # Ignore any zeroes
    concept_ids.discard(0)
    return concept_ids


def to_int(value: Any) -> int | None:
    """Convert value to int if possible, else return None."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _set_field_values(
    row: dict[str, str], fields: Collection[str], new_value: str
) -> dict[str, str]:
    for field in fields:
        if field in row:
            row[field] = new_value
    return row


def update_row(
    row: dict[str, str],
    target_concept: Concept,
    is_new: bool,
) -> dict[str, str]:
    """Update all Usagi file fields where applicable."""
    # The list below is a superset of the fields in Usagi
    # save/review/STCM files. As these are sometimes manually
    # added/modified, the code below simply checks for all possible
    # fields whether they are present in the original Usagi file and
    # updates values where needed.

    # These fields should only be set when the old mapping is replaced
    if is_new:
        row = _set_field_values(row, CONCEPT_ID_COLUMNS, f"{target_concept.concept_id}")
        row = _set_field_values(row, ["mappingStatus"], "UNCHECKED")
        row = _set_field_values(row, ["equivalence"], "UNREVIEWED")
        row = _set_field_values(row, ["statusSetBy", "createdBy"], "UpdateBot")
        row = _set_field_values(row, ["statusSetOn", "createdOn"], f"{int(time())}")

    fields = ["conceptName", "targetConceptName"]
    row = _set_field_values(row, fields, f"{target_concept.concept_name}")
    row = _set_field_values(row, ["domainId", "targetDomainId"], f"{target_concept.domain_id}")
    fields = ["targetVocabularyId", "target_vocabulary_id"]
    row = _set_field_values(row, fields, f"{target_concept.vocabulary_id}")
    sc = target_concept.standard_concept
    row = _set_field_values(row, ["targetStandardConcept"], f"{'' if sc is None else sc}")
    row = _set_field_values(row, ["targetChildCount", "targetParentCount"], "")
    row = _set_field_values(row, ["targetConceptClassId"], f"{target_concept.concept_class_id}")
    row = _set_field_values(row, ["targetConceptCode"], f"{target_concept.concept_code}")
    start_date = f"{target_concept.valid_start_date.strftime(USAGI_DATE_FORMAT)}"
    row = _set_field_values(row, ["targetValidStartDate"], start_date)
    end_date = f"{target_concept.valid_end_date.strftime(USAGI_DATE_FORMAT)}"
    row = _set_field_values(row, ["targetValidEndDate"], end_date)
    ir = target_concept.invalid_reason
    return _set_field_values(row, ["targetInvalidReason"], f"{'' if ir is None else ir}")


def get_new_lines(
    line: dict[str, str],
    new_mappings: dict[int, NewMap | None],
    concept_lookup: dict[int, Concept] | None = None,
) -> list[dict[str, str]]:
    """Return updated Usagi file line(s)."""
    target_concept_id_col = next(col for col in CONCEPT_ID_COLUMNS if col in line)
    target_concept_id = to_int(line[target_concept_id_col])
    new_map = new_mappings.get(target_concept_id)
    new_line = line.copy()
    new_lines = []

    # Target concept was non-standard; new mappings available
    if new_map is not None:
        for concept in new_map.concepts:
            new_lines.append(update_row(new_line.copy(), concept, is_new=True))

        # If there are also MAPS_TO_VALUE relationships, add more lines
        if new_map.value_as_concept:
            for value_concept in new_map.value_as_concept:
                value_map_line = line.copy()
                value_map_line["mappingType"] = "MAPS_TO_VALUE"
                new_lines.append(update_row(value_map_line, value_concept, is_new=True))
        return new_lines

    # No new mappings; update concept properties if concept_lookup is provided.
    # It can also be that the target_concept_id doesn't exist in the user's
    # database, therefore check if concept exists in concept_lookup
    if concept_lookup is None or target_concept_id not in concept_lookup:
        return [new_line]
    up_to_date_concept = concept_lookup[target_concept_id]
    return [update_row(new_line.copy(), up_to_date_concept, is_new=False)]


def write_usagi_file(
    usagi_file: Path,
    new_mappings: dict[int, NewMap | None],
    overwrite: bool,
    concept_lookup: dict[int, Concept] | None = None,
):
    out_dir = usagi_file.parent
    out_file = out_dir / f"{usagi_file.stem}_{strftime('%Y-%m-%dT%H%M%S')}.csv"

    with usagi_file.open("r") as f_in, out_file.open("w") as f_out:
        reader = csv.DictReader(f_in, delimiter=",")
        out_header = list(reader.fieldnames)
        # Usagi review and STCM files don't contain the mapping type,
        # but it is essential for any MAPS_TO_VALUE relationships.
        if "mappingType" not in out_header:
            out_header.append("mappingType")
        writer = csv.DictWriter(f_out, delimiter=",", fieldnames=out_header)
        writer.writeheader()
        for line in reader:
            new_lines = get_new_lines(line, new_mappings, concept_lookup)
            for new_line in new_lines:
                writer.writerow(new_line)
    if overwrite:
        out_file = out_file.replace(usagi_file)
    logger.info(f"Updated Usagi file available at: {out_file}")


def write_mapping_paths(usagi_file: Path, new_maps: list[NewMap]) -> None:
    out_dir = usagi_file.parent
    out_file = out_dir / f"{usagi_file.stem}_map_path_{strftime('%Y-%m-%dT%H%M%S')}.yml"
    map_paths_as_dict = {}
    for nm in new_maps:
        map_paths_as_dict.update(nm.to_map_path_data())
    write_yaml_file(map_paths_as_dict, out_file)


def write_yaml_file(contents: dict | list, out_path: Path) -> None:
    """Write dict to a YAML file."""
    with out_path.open("w", encoding="utf8") as out:
        yaml.dump(contents, out)
