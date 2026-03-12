# Development

## Setup steps

Make sure the following tooling is installed:
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Install the project and dev dependencies via `uv sync --all-groups`.

Then set up the git hook scripts via `uv run pre-commit install`.

## Nox sessions

Run `nox -l` for a list of available nox sessions, or simply run `nox`
to run the ruff linter and the pytest suite for all supported Python versions.

## Releasing

Kotobuki uses [semantic versioning](https://semver.org/).

New releases are made from the main branch. Whenever making a new release,
check the following:
- CHANGELOG.md includes a summary of all changes since the last release.
- The package version stated in pyproject.toml reflects the release you want
  to make.

Once you create the release on GitHub, the release will be automatically
published to PyPI via the `publish` GitHub action.
