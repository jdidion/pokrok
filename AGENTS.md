# AGENTS.md

Guidance for agents and contributors working on pokrok.

## Project

pokrok is a small pure-Python library: a single API over several progress-bar
backends (tqdm, progressbar2, halo, and a stdlib-logging fallback), selected at
runtime via entry points.

- Trunk branch: `main`
- Packaging: `pyproject.toml` only (setuptools build backend, setuptools-scm
  for dynamic versioning). There is no `setup.py`/`setup.cfg`/`versioneer.py`.
- Python: `>=3.10`.
- Tooling: managed with [uv](https://docs.astral.sh/uv/).

## Build / test / lint

```bash
uv sync                                   # create the venv, install dev deps
uv run pytest --cov --cov-report term-missing   # run tests with coverage
uv run ruff check pokrok tests            # lint
uv run ruff format pokrok tests           # format
uv build                                  # build sdist + wheel into dist/
```

The test suite exercises the real backend libraries (tqdm, progressbar2, halo,
stdlib logging), which are installed via the `dev` dependency group, so tests
need no mocking of the underlying progress-bar packages.

## Versioning / release

The version is derived from git tags by setuptools-scm; do not hardcode a
version in `pyproject.toml`. To cut a release, tag the commit (e.g. `0.3.0`)
and build:

```bash
git tag 0.3.0
uv build
```

Publishing to PyPI is a human step (e.g. `uv publish`); agents must not push
tags or publish.

## Conventions

- Keep `pyproject.toml` the single source of build configuration.
- Use `importlib.metadata` / `importlib.resources` (not `pkg_resources`).
- Each backend lives in `pokrok/plugins/<name>.py` and is wired in via the
  `[project.entry-points.pokrok]` table.
