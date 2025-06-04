import logging
from collections.abc import Sequence

from omop_cdm.regular.cdm54.tables import Concept

from .relationship import NewMap

logger = logging.getLogger(__name__)


def log_missing_in_db(found_concepts: Sequence[Concept], all_concept_ids: set[int]) -> None:
    concept_ids_in_db = {c.concept_id for c in found_concepts}
    missing_in_db = {c_id for c_id in all_concept_ids if c_id not in concept_ids_in_db}
    if missing_in_db:
        logger.warning(
            f"😕 {len(missing_in_db)} concepts could not be found in the "
            f"database, these will be ignored: {missing_in_db}\n"
        )
    else:
        logger.info("All target concepts found in database 🥳")


def log_remapped_concepts(new_mappings: dict[int, NewMap | None]) -> None:
    n_mapped = len([v for v in new_mappings.values() if v is not None])
    if n_mapped > 0:
        logger.info(f"{n_mapped}/{len(new_mappings)} could be remapped ✨✨")
    else:
        logger.info("No standard concepts could be found ☹️")
    unmapped = [c_id for c_id, v in new_mappings.items() if v is None]
    if unmapped:
        logger.info(f"The following concept_ids could not be remapped: {unmapped}")
