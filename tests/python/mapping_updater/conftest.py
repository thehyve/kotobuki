import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml
from omop_cdm.constants import VOCAB_SCHEMA
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.sql.ddl import CreateSchema, DropSchema
from testcontainers.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:16-alpine"
SCHEMA_MAP: dict[str, str] = {VOCAB_SCHEMA: "vocab"}

DB_SETUP_DIR = Path(__file__).parent / "db_setup"
VOCAB_DDL_FILE = DB_SETUP_DIR / "vocab_ddl.sql"
VOCAB_DATA_DIR = DB_SETUP_DIR / "vocab_data"

TEST_DATA_DIR = Path(__file__).parent / "test_data"
MAP_TO_0_USAGI_FILE = TEST_DATA_DIR / "usagi_files" / "mapping_to_0.csv"
USAGI_STCM_FILE = TEST_DATA_DIR / "stcm" / "usagi_test_stcm.csv"


@pytest.fixture(scope="session")
def pg_db_engine() -> Iterator[Engine]:
    with PostgresContainer(POSTGRES_IMAGE) as postgres:
        engine = create_engine(postgres.get_connection_url())
        engine = engine.execution_options(schema_translate_map=SCHEMA_MAP)
        yield engine


def create_schemas(schemas: set[str], conn: Connection) -> None:
    for schema in schemas:
        conn.execute(CreateSchema(schema, if_not_exists=True))


def drop_schemas(schemas: set[str], conn: Connection) -> None:
    for schema in schemas:
        conn.execute(DropSchema(schema, cascade=True, if_exists=True))


@contextmanager
def temp_schemas(engine: Engine, schemas: set[str]):
    with engine.begin() as conn:
        create_schemas(schemas, conn)
    yield
    with engine.begin() as conn:
        drop_schemas(schemas, conn)


@pytest.fixture(scope="session")
def create_vocab_tables(pg_db_engine: Engine):
    """Create vocabulary tables subset and load test data."""
    with temp_schemas(pg_db_engine, schemas=SCHEMA_MAP.values()):
        create_vocab_subset(pg_db_engine)
        load_relationship_test_data(pg_db_engine)
        yield pg_db_engine


def create_vocab_subset(engine: Engine):
    ddl_queries = text(VOCAB_DDL_FILE.read_text(encoding="utf8"))
    with engine.begin() as con:
        con.execute(ddl_queries)


def load_relationship_test_data(engine: Engine) -> None:
    for vocab_file in VOCAB_DATA_DIR.glob("*.csv"):
        table = f"vocab.{vocab_file.stem}"
        connection = engine.raw_connection()
        try:
            cursor = connection.cursor()
            statement = f"COPY {table} FROM STDIN WITH DELIMITER E'\t' CSV HEADER QUOTE E'\b';"
            with vocab_file.open("rb") as f:
                cursor.copy_expert(sql=statement, file=f)
            cursor.close()
            connection.commit()
        finally:
            connection.close()


def write_tmp_usagi_file(tmp_path: Path, original_usagi_file: Path) -> Path:
    tmp_usagi_file = tmp_path / original_usagi_file.name
    shutil.copyfile(original_usagi_file, tmp_usagi_file)
    return tmp_usagi_file


def read_yaml_file(path: Path) -> dict:
    """Read the YAML file and return as dict."""
    with path.open("rt") as f:
        return yaml.safe_load(f.read())
