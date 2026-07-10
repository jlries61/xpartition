# xpartition

Exact data partitioner: randomly partitions a table (CSV) into learning, test,
and holdout partitions — or cross-validation folds — balanced on one or more
fields. Installable Python package (src layout): `xpartition` console script
(`src/xpartition/cli.py`) wrapping the library function `xpartition()`
(`src/xpartition/__init__.py`).

## SSD Convention

This project uses Shippable States Development. SSD working artifacts live in
`.ssd/` (selectively gitignored — design docs commit, machine state stays local).
Primary SSD commands:

- `/ssd start` — Walking Skeleton for new features
- `/ssd feature` — daily feature loop (architect → systems-designer → coder → review)
- `/ssd gate` — shippable-state check
- `/ssd milestone` — post-sprint audit

See `.ssd/README.md` for the artifact tree.

## Stack

- Language: Python 3 (>= 3.9), src layout under `src/xpartition/`
- Dependencies: pandas (plus stdlib argparse, random, fractions)
- Platform: headless CLI / importable library

## Test / Lint / Build

- Tests: `pytest` (tests/, runs against the src/ working tree via pythonpath)
- Linter: none yet
- Packaging: pyproject.toml (setuptools); RPM via `./build-rpm.sh` + xpartition.spec
- CI: GitHub Actions — pytest matrix (3.9/3.13/3.14), sdist/wheel build + twine
  check, pyproject↔spec version-agreement check
- Version lives in TWO files that must agree: pyproject.toml and
  xpartition.spec (see RELEASING.md); CI enforces this

## Deployment

- Distribution: GitHub repo (github.com/jlries61/xpartition); pushing a v* tag
  creates a GitHub Release with sdist + wheel attached
- No PyPI release yet — the name `xpartition` is taken; renaming is a
  prerequisite (see RELEASING.md § 5)
