# Maintenance

## Local checks

```bash
uv sync --frozen
uv run pytest --cov --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run mkdocs build --strict
uv build --no-sources
```

The test matrix covers Python 3.9 through 3.14 and NumPy 1.26 and 2.x.

## Documentation rules

- Keep `README.md` short and task-oriented.
- Keep English pages as the default navigation source.
- Put the Simplified Chinese translation in the matching `.zh.md` page.
- Build with `--strict` so broken links and configuration warnings fail CI.

The documentation site is built and published from `main` by GitHub Actions.

## Release

Update the version in `pyproject.toml`, refresh `uv.lock`, and push a `vX.Y.Z`
tag. The release workflow builds the source distribution and wheel, creates or
updates the GitHub Release, and publishes the same artifacts to PyPI through
Trusted Publishing.
