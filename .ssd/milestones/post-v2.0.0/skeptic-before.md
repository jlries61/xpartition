---
skill: codebase-skeptic
version: 1.4.0
produced_at: 2026-07-09T14:30:00-07:00
produced_by: claude-fable-5
project: xpartition
scope: SHA fac93f4 (v2.0.0) — src/xpartition/{__init__.py,cli.py}, tests/test_xpartition.py, pyproject.toml, .github/workflows/ci.yml, xpartition.spec, build-rpm.sh, README.md, RELEASING.md
consumed_by: [refactor, code-reviewer, ssd]
finding_counts:
  structural_risk: 0
  problem: 3
  concern: 8
findings:
  - id: SK-01
    severity: problem
    title: Fractional nlearn/ntest/nholdout silently produce a wrong partition
  - id: SK-02
    severity: problem
    title: Local pytest exercises the installed package, not the src/ working tree
  - id: SK-03
    severity: problem
    title: xpartition() reseeds the global random-module RNG (hidden side effect)
  - id: SK-04
    severity: concern
    title: No input validation (zero/negative proportions, cv+nlearn conflicts)
  - id: SK-05
    severity: concern
    title: CLI error UX — raw tracebacks for bad numeric options and unreadable files
  - id: SK-06
    severity: concern
    title: Dead code and archaic option parsing (unused ncv, getopt, COMMA constant)
  - id: SK-07
    severity: concern
    title: CI matrix does not test the claimed floor (3.8) nor the dev interpreter (3.14); no lint
  - id: SK-08
    severity: concern
    title: Version hand-maintained in two files with no automated agreement check
  - id: SK-09
    severity: concern
    title: Working-tree hygiene — example outputs and editor backups neither tracked nor ignored
  - id: SK-10
    severity: concern
    title: No release artifact channel — nothing attached to GitHub releases
  - id: SK-11
    severity: concern
    title: Documentation drift — CLAUDE.md describes the pre-2.0 repo; README typos
voices_activated: [fowler, uncle-bob, beck, humble, jobs, wozniak]
posture: sound
gate_pass: true
---

# Codebase Review: `xpartition`

**Reviewed:** 2026-07-09
**Scope:** Full repository at SHA `fac93f4` (v2.0.0, immediately post-ship of the packaging overhaul)
**Domain:** Exact data partitioner — splits a CSV/DataFrame into learning/test/holdout samples or CV folds in exact proportions, optionally balanced (stratified) on one or more fields
**Stack:** Python 3 (pandas + stdlib), setuptools/pyproject packaging, pytest, GitHub Actions CI, RPM spec for Fedora
**Voices Activated:** Fowler, Uncle Bob, Beck, Humble, Jobs, Wozniak

---

## Overall Posture

```
✅ Sound — defensible architecture, addressable issues
```

**In one sentence:** A small, genuinely elegant tool that just gained real engineering infrastructure (packaging, tests, CI) — its remaining problems are silent-wrong-answer edge cases at the input boundary and a local test loop that quietly tests the wrong copy of the code.

---

## Fowler — Architecture & Evolutionary Design

> *Refactoring, software smells, distribution decisions, change-enabling structure*

### Findings

**⚠ SK-06 — Dead code and 2003-era option parsing**
`src/xpartition/__init__.py:63`, `src/xpartition/cli.py:14,21,65-95`
`ncv = cv` is assigned and never read — a leftover from a prior design. The CLI is built on `getopt` with a hand-rolled `if/elif` ladder and a `COMMA = ","` constant; every option added means touching three places (USAGE string, longopts list, dispatch ladder) — mild shotgun surgery for a CLI this small. `argparse` would collapse the ladder, generate `--help` from declarations, and give typed, validated option values for free — which would also close most of SK-05.

**⚠ SK-08 — Version hand-synced across two files**
`pyproject.toml:7`, `xpartition.spec:2`
RELEASING.md honestly documents that the version lives in two places that "must agree." Documented drift is still drift waiting to happen; the first mismatched release will ship an RPM claiming the wrong version. A five-line CI step comparing the two values turns a process rule into a checked invariant.

### Fowler's Recommendation
The architecture (one pure function + one thin CLI wrapper) is exactly right for the problem — do not add layers. Spend the refactoring budget at the edges: replace `getopt` with `argparse` in one small PR, delete `ncv`, and add a version-agreement check to CI.

---

## Uncle Bob — Code Structure & SOLID

> *Clean code, dependency direction, modularity, naming, separation of concerns*

### Findings

**🔴 SK-03 — `xpartition()` mutates global interpreter state**
`src/xpartition/__init__.py:72` — `random.seed(rseed)`
A library function that reseeds the process-wide `random` module is a side effect hidden behind an innocent name. Verified empirically: after calling `xpartition(df)`, the caller's subsequent `random.random()` sequence is different from what it would have been — any consumer relying on their own seeding (simulations, other samplers, test fixtures) gets silently corrupted reproducibility. This was harmless when xpartition was a standalone script; v2.0.0 made it an importable package and turned the shortcut into a contract violation. The fix is mechanical: `rng = random.Random(rseed)` and use `rng.uniform(...)`.

**⚠ Naming nits (fold into SK-06)**
`nlearn`/`ntest`/`nholdout` read as counts ("records per assignment cycle" per the USAGE text) but are typed as floats and documented as "proportion or count" in the docstring — the name, the type, and the docs disagree about what this parameter is. Resolving SK-01 will force this to be decided.

### Uncle Bob's Recommendation
Instantiate a local `random.Random(rseed)` inside `xpartition()`. This is a one-line dependency-direction fix: the function should own its randomness source, not borrow the process's.

---

## Beck — Tests & Feedback Loops

> *Test quality, TDD signals, YAGNI, incremental design, feedback cycle length*

### Findings

**🔴 SK-02 — Local pytest tests the installed copy, not the working tree**
`tests/test_xpartition.py:11`, `pyproject.toml:39-40`
There is no `pythonpath` setting, no editable-install instruction, and no src-layout import shim — so `import xpartition` in the tests resolves to `/usr/lib/python3.14/site-packages/xpartition`, as the coverage report proves. Concretely: edit `src/xpartition/__init__.py`, run `pytest`, and the suite passes green against the *old installed code*. That is the worst kind of feedback loop — fast, confident, and wrong. CI is immune (it runs `pip install .` first), which makes the trap purely local and therefore easy to never notice. Fix: add `pythonpath = ["src"]` to `[tool.pytest.ini_options]`, or document `pip install -e .[test]` as the dev setup in RELEASING.md — either restores truth to the loop.

**⚠ SK-04 (test-gap aspect) — The suite only exercises the blessed path**
`tests/test_xpartition.py`
The 15 tests are good behavior tests — exact counts, balance, reproducibility, frame non-mutation, CLI end-to-end via subprocess, all in 3.6 s. What's missing is the hostile-input half: fractional proportions (SK-01 would have been caught), all-zero proportions, negative values, `--cv` combined with `--nlearn`, malformed CSV, non-numeric option values. Every finding in this report that reached 🔴 lives in territory the suite doesn't visit.

**Credit where due:** the tests assert behavior, not implementation — `test_input_frame_not_modified` and `test_row_order_and_data_preserved` are exactly the contracts a caller cares about. No confidence theater here; the coverage that exists is honest.

### Beck's Recommendation
Fix the import resolution *first* (it's one line), because until then every other local test-driven fix is built on sand. Then write the failing tests for SK-01/SK-04 before touching the validation code — this codebase is small enough to do it properly.

---

## Humble — Delivery Pipeline & Deployment

> *Pipeline completeness, manual steps, rollback, environment parity, deploy safety*

### Findings

**⚠ SK-07 — The CI matrix doesn't test what the package claims or what the developer runs**
`.github/workflows/ci.yml:12`, `pyproject.toml:15`
`requires-python = ">=3.8"` but the matrix tests 3.9 and 3.13 — the claimed floor is unverified (and 3.8 is past EOL; the honest fix is raising the floor, not widening the matrix). Meanwhile the development machine runs 3.14, which the matrix also skips. There is no lint/format step, so style drift has no backstop. The pipeline that exists is properly enforced — tests and `twine check` both block on failure, no `continue-on-error` anywhere — good.

**⚠ SK-10 — Releases produce no downloadable artifact**
`RELEASING.md`, `.ssd/project.yml` (`distribution.channel: TBD`)
The release process ends at a git tag; the sdist, wheel, and RPM built by `build-rpm.sh` live only on the maintainer's disk. A user who wants v2.0.0 must clone and build. PyPI is blocked by the name collision (documented), but GitHub Releases is available today: a tag-triggered workflow that builds and attaches sdist + wheel (and optionally the RPM) would give the project an actual distribution channel and make rollback "install the previous release's artifact" instead of "rebuild from an old checkout."

**Operational failure modes sweep (mandatory):** queues, caching, databases, external service dependencies, and secrets/config are all **not applicable** — this is a stateless batch CLI/library with no network, no persistence beyond its input/output files, and no configuration beyond argv. Deploy pipeline verdicts: smoke tests *enforced* (CI blocks); rollback = installing the prior tag/RPM, workable but artifact-less today (SK-10); feature flags absent and *appropriately* so for a stateless library — the SSD flag rule is N/A here.

### Humble's Recommendation
Raise `requires-python` to `>=3.9` (matching the tested floor), add 3.14 to the matrix, and add a tag-triggered release workflow uploading the build artifacts to GitHub Releases. All three are pipeline-only changes with zero code risk.

---

## Jobs — Product Judgment & Coherence

> *Simplicity, API design, feature coherence, configuration surface, user model*

### Findings

**🔴 SK-01 — Fractional proportions silently produce garbage**
`src/xpartition/cli.py:91-95`, `src/xpartition/__init__.py:77-89`
The docstring says nlearn is a "proportion or count," the CLI parses it as `float` — so `xpartition --nlearn=0.8 --ntest=0.2` is an entirely natural thing to type. Verified: it produces a file where **every record is "Learn"** — no error, no warning, a well-formed output that is simply wrong. (The integer cycle counter `num` resets to 0 whenever it reaches `denom=1.0`, so it never escapes the Learn branch.) Likewise `--nlearn=0 --ntest=0` silently yields all-Holdout. A user who doesn't tabulate the output ships a model with no test sample. This is the product failing exactly the person it was designed for. Decide the contract — either support fractions (normalize them) or reject them loudly — but never emit a silently wrong partition.

**⚠ SK-05 — Failure UX is raw tracebacks**
`src/xpartition/cli.py:83-95,112`
`--cv=ten` dies with a `ValueError` traceback; a missing or malformed input file dies with a pandas stack dump. The `--bogus` case, by contrast, prints a clean two-line message with a `--help` pointer (and the test suite pins it) — that's the standard the other failure paths should meet. Also unhandled: `--cv=5 --nlearn=4` silently ignores `--nlearn`, hiding a user's contradictory intent.

**⚠ SK-11 (README aspect) — Docs polish**
`README.md:36` — "systematically assign *then* to the desired *fields*" (them/partitions); line 2 says "training" where the tool's own vocabulary is "Learn/learning." Small, but this is the front door.

### Jobs's Recommendation
One rule: the tool never writes a wrong answer quietly. Validate inputs at the CLI boundary, fail with one clear sentence, and make `--nlearn=0.8` either work correctly or refuse to run.

---

## Wozniak — Engineering Economy & Elegance

> *Unnecessary complexity, algorithmic waste, abstraction tax, genuine ingenuity*

### Findings

**Genuinely elegant core — worth preserving as-is**
`src/xpartition/__init__.py:74-102`
The central algorithm deserves credit: attach a random sort key, sort by (balance fields, random key), assign cyclically from a precomputed pattern, sort back by index. Exact proportions guaranteed by construction, stratification for free from the sort order, O(n log n), ~30 lines, no dependencies beyond pandas. This is "simplicity achieved through understanding." Do not let remediation complicate it.

**⚠ (fold into SK-06) — Minor waste, none of it structural**
The per-row `dict` + `pd.Series` construction of random keys (`__init__.py:93-97`) does in ~4 lines and O(n) Python-loop time what `rng.random()` in a list comprehension or `np.random` vectorization does faster — at a million rows this is the slow spot, but it is linear and nobody has complained. The `assign` list is rebuilt implicitly identical for every indicator (correct, since it's reused — fine). Duplicate-index DataFrames get a slightly degraded shuffle (duplicate labels share one sort key via the dict) but verified to still produce well-formed output — worth one docstring sentence, not code.

### Wozniak's Recommendation
Leave the algorithm alone. If anyone ever profiles a real bottleneck, vectorize the sort-key generation with numpy — until then, it's premature.

---

## Synthesis

### Dominant Failure Mode
**Trust at the boundaries.** The core algorithm is correct and elegant, but the package trusts its inputs (SK-01, SK-04, SK-05), trusts the process RNG (SK-03), trusts that the tested code is the edited code (SK-02), and trusts that two hand-edited version strings agree (SK-08). Every 🔴 finding is a place where that trust fails *silently* — the tool's whole value proposition is exactness, and its failure modes are inexact output with a green checkmark.

### Highest-Leverage Intervention
Fix SK-02 first (`pythonpath = ["src"]` in pyproject — one line): until local tests test the working tree, every subsequent fix's red-green signal is unreliable. Then SK-01 + SK-04 together as one "validate the input contract" change with tests written first — that closes the only user-facing silent-wrong-answer path.

### Forward-Looking Pass
- **Scale:** At 10× data the first thing to hurt is the per-row Python loop building sort keys plus whole-table memory residency — degraded but linear, no cliff (SK-06 note).
- **Team:** A new contributor will edit `src/`, run `pytest`, see green from the stale installed copy, and open a PR whose changes were never executed locally — SK-02 is precisely the first-month trap.
- **Incident:** The hardest 3am diagnosis is "my holdout sample is empty / my split is 100% Learn" from fractional or zero proportions, because the output is well-formed and the bug leaves no error anywhere (SK-01).
- **Friday deploy:** A release (version bump in two hand-synced files, hand-built RPM, manual tag) carries more risk than it should and is caught by no automated check — SK-08/SK-10; conversely nothing in this stateless codebase *should* be Friday-scary once those are automated.

(All four answers are known; the F-findings are already captured as SK-01, SK-02, SK-08, SK-10 — no new F-prefixed items needed.)

### Prioritized Remediation Order

| Priority | Action | Finding | Voice(s) | Effort | Risk if Deferred |
|---|---|---|---|---|---|
| 1 | Point local pytest at src (`pythonpath = ["src"]`) and document `pip install -e .[test]` | SK-02 | Beck | S | High — false green locally |
| 2 | Validate proportion/cv inputs; reject or correctly support fractional values; tests first | SK-01, SK-04 | Jobs, Beck | S–M | High — silent wrong output |
| 3 | Use `random.Random(rseed)` instance instead of global `random.seed` | SK-03 | Uncle Bob | S | Med — corrupts consumers' RNG |
| 4 | CLI error handling: clean messages for bad option values / unreadable input; warn on `--cv`+`--nlearn` | SK-05 | Jobs | S | Med |
| 5 | Migrate getopt→argparse; delete `ncv`; align docstring/USAGE wording on proportions | SK-06 | Fowler, Uncle Bob | M | Low |
| 6 | CI: raise floor to `>=3.9`, add 3.14 to matrix, add version-agreement check (pyproject vs spec) | SK-07, SK-08 | Humble, Fowler | S | Med — first mismatched release |
| 7 | Tag-triggered GitHub Release workflow attaching sdist/wheel (+RPM) | SK-10 | Humble | M | Low |
| 8 | Gitignore or relocate example outputs (`b*.csv`, `README.html`, `Data/`, `xpartition~`) | SK-09 | — | S | Low |
| 9 | Fix README typos; refresh CLAUDE.md (it still says "no tests, no packaging") | SK-11 | Jobs | S | Low |

*Effort: S = hours, M = days, L = weeks or more*

### Hook for `/code-reviewer`

| Finding | Files/patterns | Trigger for code-reviewer |
|---|---|---|
| SK-01/SK-04 input contract | `src/xpartition/__init__.py`, `src/xpartition/cli.py` | Any PR touching parameter handling: verify no path emits a partition without validating nlearn/ntest/nholdout/cv |
| SK-02 test-target integrity | `pyproject.toml`, `tests/**` | Any PR adding tests: confirm they import the src tree, not site-packages |
| SK-03 RNG isolation | `src/xpartition/__init__.py` | Any PR touching randomness: no global `random.seed`; must use an instance RNG |
| SK-08 version sync | `pyproject.toml`, `xpartition.spec` | Any version-bump PR: check both files + spec %changelog agree |

---

## Caveats & Scope Limitations

None material. Review had full visibility into all source, tests, packaging, and CI configuration. Runtime claims (SK-01, SK-02, SK-03) were verified empirically against the working tree, not inferred. The RPM build (`build-rpm.sh` / `xpartition.spec`) was reviewed statically but not executed during this audit.

---

*Review conducted using the Codebase Skeptic framework. Findings represent the application of
established software engineering authority to observed evidence, not personal preference.*
