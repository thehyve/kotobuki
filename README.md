# kotobuki

[![tests](https://github.com/thehyve/kotobuki/actions/workflows/tests.yml/badge.svg)](https://github.com/thehyve/kotobuki/actions/workflows/tests.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/kotobuki.svg)](https://pypi.org/project/kotobuki/)
[![License](https://img.shields.io/pypi/l/kotobuki.svg)](https://github.com/thehyve/kotobuki/blob/main/LICENSE)

kotobuki is a Python package that can update custom mappings created in Usagi that have become
outdated in a new release of the OHDSI vocabularies.

## Installation

kotobuki requires Python 3.11+ and is available on PyPI:

```shell
pip install kotobuki
```

Depending on the type of database you have, you'll also need to install the required python
adapter library.
E.g. for postgresql, you can use [psycopg2](https://pypi.org/project/psycopg2/).

See SQLAlchemy docs for a list of supported [dialects](https://docs.sqlalchemy.org/en/20/dialects/).

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
