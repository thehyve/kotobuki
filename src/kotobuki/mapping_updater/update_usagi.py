import logging
import sys
from importlib.metadata import version
from pathlib import Path

from omop_cdm.constants import VOCAB_SCHEMA
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .db import (
    NewMap,
    find_new_mapping,
    query_concepts,
)
from .io import (
    get_target_concepts,
    write_mapping_paths,
    write_usagi_file,
)
from .log import (
    log_missing_in_db,
    log_remapped_concepts,
)

logger = logging.getLogger(__name__)


def update_usagi_file(
    engine: Engine,
    vocab_schema: str,
    usagi_file: Path,
    allow_homonyms: bool = False,
    case_insensitive_homonyms: bool = False,
    write_map_paths: bool = False,
    inspect_only: bool = False,
    overwrite: bool = False,
    update_all: bool = False,
):
    """
    Parse an Usagi exported file to update non-standard concepts.

    :param engine: SQLAlchemy engine to connect with.
    :param vocab_schema: Schema containing the vocabulary tables.
    :param usagi_file: Usagi exported file (save/review/STCM).
    :param allow_homonyms: If no standard concept can be found through
        concept relationships, try to find it through concepts with the
        same concept name. It is strongly recommended to index the
        concept_name column when using this.
    :param write_map_paths: Write an additional file that shows for each
        remapped concept, through which mapping relationships the new
        target concept was determined.
    :param inspect_only: Instead of writing updated mappings to a file,
        only show results in the console.
    :param overwrite: Overwrite the existing Usagi file (otherwise a new
        file is written).
    :param update_all: Also update fields of concepts that don't get a
        new mapping, but do have outdated properties (e.g. changed
        domain_id).
    :return: None
    """
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)
    logger.info(f"Running kotobuki v{version('kotobuki')}")

    if inspect_only and overwrite:
        raise ValueError("inspect_only and overwrite cannot both be True.")

    logging.info(f"Parsing Usagi save file {usagi_file.name}")
    concept_ids = get_target_concepts(usagi_file)
    logging.info(f"{len(concept_ids)} distinct target concepts found in file")
    if not concept_ids:
        return

    engine = engine.execution_options(schema_translate_map={VOCAB_SCHEMA: vocab_schema})

    with Session(engine) as session, session.begin():
        concepts = query_concepts(concept_ids, session)
        log_missing_in_db(found_concepts=concepts, all_concept_ids=concept_ids)

        non_standard = {c for c in concepts if c.standard_concept != "S"}
        if not non_standard:
            logger.info("All target concepts are already standard 😍")
            if not update_all:
                return
        else:
            logger.info(f"{len(non_standard)} target concepts are non-standard")

        new_mappings: dict[int, NewMap | None] = {c.concept_id: None for c in non_standard}

        logger.info("Querying database for standard concepts...")
        for concept in non_standard:
            new_map = find_new_mapping(concept, allow_homonyms, case_insensitive_homonyms, session)
            new_mappings[concept.concept_id] = new_map
        log_remapped_concepts(new_mappings)

        if write_map_paths:
            logger.info("Writing mapping paths file")
            new_maps = [nm for nm in new_mappings.values() if nm is not None]
            write_mapping_paths(usagi_file, new_maps)

        if inspect_only:
            return

        logger.info("Writing updated Usagi file")
        if update_all:
            concept_lookup = {c.concept_id: c for c in concepts}
            write_usagi_file(usagi_file, new_mappings, overwrite, concept_lookup)
        else:
            write_usagi_file(usagi_file, new_mappings, overwrite)
