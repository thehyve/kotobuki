import nox  # type: ignore

nox.options.default_venv_backend = "uv"

nox.options.sessions = [
    "tests",
    "lint",
]

python = [
    "3.11",
    "3.12",
    "3.13",
]


@nox.session(python=python)
def tests(s: nox.Session):
    s.install(".")
    s.run("uv", "pip", "install", "--group", "test")
    s.run("pytest", "--cov-report", "term-missing", "--cov=kotobuki")


@nox.session(python=False, name="format")
def format_all(s: nox.Session):
    """Format codebase with ruff."""
    s.run("uv", "run", "ruff", "format")
    # format imports according to isort via ruff check
    s.run("uv", "run", "ruff", "check", "--select", "I", "--fix")


@nox.session(python=False)
def lint(s: nox.Session):
    """Run ruff linter."""
    s.run("uv", "run", "ruff", "check")
    # Check if any code requires formatting via ruff format
    s.run("uv", "run", "ruff", "format", "--diff")
