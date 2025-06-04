#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

import click
from sqlalchemy import create_engine

from .update_usagi import update_usagi_file

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--url",
    required=True,
    help="SQLAlchemy database URL",
    type=click.STRING,
)
@click.option(
    "--schema",
    required=True,
    help="Schema containing the OHDSI vocabulary tables",
    type=click.STRING,
)
@click.option(
    "-f",
    "--usagi-file",
    required=True,
    help="A file saved or exported from Usagi",
    type=click.Path(dir_okay=False, exists=True, readable=True, path_type=Path),
)
@click.option(
    "-h",
    "--allow-homonyms",
    is_flag=True,
    default=False,
    help="If no standard concept can be found through concept relationships, "
    "try to find it through concepts with the same concept name. It is "
    "strongly recommended to index the concept_name column when using this.",
)
@click.option(
    "-m",
    "--write-map-paths",
    is_flag=True,
    default=False,
    help="Write an additional file that shows for each remapped concept, "
    "through which mapping relationships the new target concept was determined.",
)
@click.option(
    "-s",
    "--inspect-only",
    is_flag=True,
    default=False,
    help="Instead of writing updated mappings to a file, only show results in the console.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the existing Usagi file (otherwise a new file is written).",
)
def _update_usagi_cli(
    url: str,
    schema: str,
    usagi_file: Path,
    allow_homonyms: bool,
    write_map_paths: bool,
    inspect_only: bool,
    overwrite: bool,
) -> None:
    """
    Parse an Usagi saved/exported file to update non-standard concepts.
    """
    engine = create_engine(url)
    update_usagi_file(
        engine,
        schema,
        usagi_file,
        allow_homonyms,
        write_map_paths,
        inspect_only,
        overwrite,
    )


def main():
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.DEBUG)
    _update_usagi_cli()


if __name__ == "__main__":
    main()
