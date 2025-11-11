# kotobuki

[![tests](https://github.com/thehyve/kotobuki/actions/workflows/tests.yml/badge.svg)](https://github.com/thehyve/kotobuki/actions/workflows/tests.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/kotobuki.svg)](https://pypi.org/project/kotobuki/)
[![License](https://img.shields.io/pypi/l/kotobuki.svg)](https://github.com/thehyve/kotobuki/blob/main/LICENSE)

kotobuki is a Python package that can update custom mappings created in Usagi that have become
outdated in a new release of the OHDSI vocabularies.

## Installation

kotobuki requires Python 3.11+ and is available on [PyPI](https://pypi.org/project/kotobuki/).

Depending on the type of database you have, you'll also need to install the required python
adapter library.
E.g. for postgresql, you can use [psycopg2](https://pypi.org/project/psycopg2/).

See SQLAlchemy docs for a list of supported [dialects](https://docs.sqlalchemy.org/en/20/dialects/).

As kotobuki is intended to be used as a standalone tool, the recommended method of installation is
in an isolated (temporary) environment.

E.g. if using [uv](https://docs.astral.sh/uv/) with a postgresql database:

```shell
uvx --with psycopg2 --from kotobuki update-usagi-file --help
```

Or within a Jupyter notebook:

```shell
uv run --with jupyter,psycopg2,kotobuki jupyter lab
```


## Usage
See [User documentation](https://github.com/thehyve/kotobuki/blob/main/docs/kotobuki.md)

## Development

### Setup steps

Make sure the following tooling is installed:
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Install the project and dev dependencies via `uv sync --all-groups`.

Then set up the git hook scripts via `uv run pre-commit install`.

### Nox sessions

Run `nox -l` for a list of available nox sessions, or simply run `nox`
to run the ruff linter and the pytest suite for all supported Python versions.
