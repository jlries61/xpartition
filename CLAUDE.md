# xpartition

Exact data partitioner: randomly partitions a table (CSV) into learning, test,
and holdout partitions — or cross-validation folds — balanced on one or more
fields. Python CLI script (`xpartition`) plus an importable package function
(`__init__.py` re-exports `xpartition()` from the script).

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

- Language: Python 3 (single script + package `__init__.py`; no pyproject.toml yet)
- Dependencies: pandas (plus stdlib getopt, random, sys)
- Platform: headless CLI / importable library

## Test / Lint / Build

- Tests: none yet
- Linter: none yet
- Packaging: none yet (no pyproject.toml / setup.py)

## Deployment

- Distribution: GitHub repo only (github.com/jlries61/xpartition); no PyPI release yet
