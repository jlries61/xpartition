---
skill: refactor
version: 1.3.0
produced_at: 2026-07-09T14:45:00-07:00
produced_by: claude-fable-5
project: xpartition
scope: post-v2.0.0
consumed_by: [code-reviewer, ssd]
input_artifact: .ssd/milestones/post-v2.0.0/skeptic-before.md
items:
  - id: R1
    cites: [SK-02]
    pattern: fix-test-target
    files: [pyproject.toml, RELEASING.md]
    budget_hours: 0.5
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
  - id: R2
    cites: [SK-01, SK-04]
    pattern: guard-clauses
    files: [src/xpartition/__init__.py, src/xpartition/cli.py, tests/test_xpartition.py]
    budget_hours: 3
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
  - id: R3
    cites: [SK-03]
    pattern: encapsulate-global-state
    files: [src/xpartition/__init__.py, tests/test_xpartition.py]
    budget_hours: 1
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
  - id: R4
    cites: [SK-05, SK-06]
    pattern: replace-parser
    files: [src/xpartition/cli.py, src/xpartition/__init__.py, tests/test_xpartition.py]
    budget_hours: 4
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
  - id: R5
    cites: [SK-07, SK-08]
    pattern: pipeline-hardening
    files: [.github/workflows/ci.yml, pyproject.toml]
    budget_hours: 2
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: true
  - id: R6
    cites: [SK-10]
    pattern: release-automation
    files: [.github/workflows/release.yml, RELEASING.md]
    budget_hours: 3
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: true
  - id: R7
    cites: [SK-09]
    pattern: repo-hygiene
    files: [.gitignore]
    budget_hours: 0.5
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
  - id: R8
    cites: [SK-11]
    pattern: docs-repair
    files: [README.md, CLAUDE.md]
    budget_hours: 1
    touches_failure_modes: false
    touches_observability: false
    touches_deploy_path: false
---

# Refactor Plan — Milestone post-v2.0.0

Input: [skeptic-before.md](skeptic-before.md) (SK-01…SK-11). Every item cites its finding;
nothing here is uncited. Items are ordered by dependency and leverage, not severity alone —
R1 must land first because it restores trust in the local test loop that every later item
relies on. Each item is one small PR/commit, independently deployable and revertable.

**Honesty note on the refactoring contract.** R2 and R4 are *corrections*, not pure
behavior-preserving refactors: they change behavior at the error boundary (inputs that today
silently produce a wrong partition will instead be rejected with a message). All currently
*correct* usage is preserved bit-for-bit. This is intentional and is the point of the milestone.

---

## R1 — Local tests must test the working tree (SK-02)

**Change:** Add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml`.
Add one line to RELEASING.md § Test noting that plain `pytest` now tests `src/` directly and
`pip install -e .[test]` is the recommended dev setup.

**Tests first?** No new tests — verification is observational: after the change, the coverage
report must cite `src/xpartition/...` paths, not `site-packages`.

**Risk / rollback:** Near-zero; revert the one line. CI unaffected (it installs the package first
and `pythonpath` merely prepends).

---

## R2 — Validate the input contract; kill the silent wrong answer (SK-01, SK-04)

**Change:** In `xpartition()`, add guard clauses before any work:
- `nlearn`, `ntest`, `nholdout` must be non-negative numbers; **fractional values are
  supported** and normalized to the smallest whole-number assignment cycle (0.8/0.2 → 4:1)
  via `fractions.Fraction.limit_denominator(10**6)`, which also absorbs float imprecision
  (1/3 means one third). Negative values raise `ValueError` naming the parameter.
  *(Maintainer direction 2026-07-09, superseding this plan's original reject-loudly default.)*
- In sample mode (`cv == 0`): `nlearn + ntest + nholdout >= 1`.
- `cv` must be a non-negative integer; in CV mode, if any of nlearn/ntest/nholdout was
  explicitly set the CLI warns to stderr that they are ignored (library: document precedence).
- `indicators` must be non-empty when provided.

In `cli.py`, catch `ValueError` from the library and exit 2 with a one-line message
(matching the existing `--bogus` UX standard).

**Tests first: yes.** Write failing tests before the fix: fractional `nlearn=0.8/ntest=0.2`
raises; all-zero proportions raise; negative values raise; `4.0` still works; CLI exits 2
with a clean stderr message (no traceback) for `--nlearn=0.8`.

**Steps:**
1. [ ] Add failing tests for every guard above
2. [ ] Add guard clauses to `xpartition()`
3. [ ] Add CLI `ValueError` → exit-2 handling
4. [ ] Confirm the 15 pre-existing tests still pass unchanged (behavior preservation for valid input)

**Risk:** A downstream caller relying on today's silent-garbage behavior breaks — that break
is the fix working. **Rollback:** revert the commit.

---

## R3 — Instance RNG instead of global seeding (SK-03)

**Change:** Replace `random.seed(rseed)` + `random.uniform(0, 1)` with
`rng = random.Random(rseed)` + `rng.uniform(0, 1)` in `src/xpartition/__init__.py`.

**Output preservation:** `random.Random(rseed)` is the same Mersenne Twister as the global
functions — identical seed produces identical draws, so partition assignments are
**bit-for-bit unchanged**. The existing reproducibility tests pin this.

**Tests first: yes.** One new test: global RNG state is unaffected by calling `xpartition()`
(seed the global module, call `xpartition`, assert the next global draw matches the no-call
expectation). Plus a pinned-output regression test (exact SAMPLE sequence for a fixed
seed/frame) written *before* the change to prove assignments don't move.

**Risk / rollback:** Minimal; single-commit revert.

---

## R4 — argparse migration + failure UX (SK-05, SK-06)

**Change:** Replace the `getopt` ladder in `cli.py` with `argparse`:
- Typed options (`type=int` for `--cv`/`--rseed`, custom non-negative-int type for the
  proportion flags) — bad values get argparse's clean two-line error and exit 2.
- `--help`/`--version` generated; USAGE string content moves into argparse help text.
- Wrap `pd.read_csv` in a try/except that reports "cannot read INFILE: <reason>" and exits 1
  instead of dumping a pandas traceback.
- Delete dead `ncv` assignment (`__init__.py:63`) and the `COMMA` constant; align the
  docstring wording with the decided contract from R2 ("relative integer cycle counts",
  dropping "proportion or count").

**Ordering note:** land after R2 so argparse types and the library guards agree on one contract.

**Tests first: yes** for the new error paths (unreadable file → exit 1 + message;
`--cv=ten` → exit 2 + clean message). The five existing CLI subprocess tests pin `--help`,
`--version`, unknown-option exit code 2, and both I/O modes — they must pass unchanged.

**Budget check:** 4h budgeted. If argparse's help formatting fights the pinned
`test_cli_help` assertion (`startswith("Usage: xpartition")`), adjust the test's assertion to
argparse's `usage: xpartition` casing in the same commit and note it — that is a deliberate,
visible UX change, not silent drift. If elapsed exceeds 6h, cut scope: keep getopt, ship only
the try/except error wrapping (SK-05), defer the parser swap.

---

## R5 — CI honesty: matrix, floor, version-agreement (SK-07, SK-08)

**Change:**
- `pyproject.toml`: `requires-python = ">=3.9"` (match the tested floor; 3.8 is EOL).
- `ci.yml`: matrix `["3.9", "3.14"]` (floor + current; 3.13 dropped as redundant middle, or
  keep all three — maintainer's call, default keep all three).
- New CI step `version-check`: fail if `pyproject.toml` version ≠ `xpartition.spec` Version
  (one grep/sed comparison), turning RELEASING.md's "must agree" prose into an enforced invariant.

**Tests first?** N/A (pipeline-only). Verify by pushing a branch with a deliberate mismatch
once, observing the red X, then reverting the mismatch — a tested gate, not release theatre.

**touches_deploy_path: true** → systems-designer re-check is satisfied by the verification
step above (the only failure mode a version-check step can introduce is a false-positive
block, which the deliberate-mismatch test exercises in both directions).

---

## R6 — Tag-triggered GitHub Release with artifacts (SK-10)

**Change:** New workflow `.github/workflows/release.yml` triggered on `v*` tags: build sdist +
wheel (`python -m build`), run `twine check`, attach both to a GitHub Release via
`gh release create` / `softprops/action-gh-release`. RPM remains a local `build-rpm.sh`
product for now (CI runners lack the Fedora rpmbuild toolchain; attaching the RPM is a
follow-up if wanted). Update RELEASING.md § 4–5 to describe the automated attach.

**touches_deploy_path: true** → the new workflow must be verified on a throwaway tag
(e.g. `v2.0.0-rc-test` on a branch, deleted afterward) before the next real release relies on it.

**Risk:** Nil to code; the workflow can fail without affecting anything existing.

---

## R7 — Working-tree hygiene (SK-09)

**Change:** Add `.gitignore` entries for README-example outputs and editor backups:
`b*.csv` is too greedy — use explicit names (`bpart*.csv`, `bcv.csv`, `bosbal.csv`),
plus `README.html`, `*~`. `Data/` is the maintainer's local sample data from 2019 — **do not
delete**; ask the maintainer whether to ignore it (`Data/`) or track it as test fixtures.
Default: add to `.gitignore` with a comment.

**Risk:** None. No tracked files are touched; nothing is deleted.

---

## R8 — Documentation repair (SK-11)

**Change:**
- README.md line 36: "systematically assign ~~then~~ **them** to the desired ~~fields~~
  **partitions**"; line 2: "training" → "learning" (match the tool's own vocabulary).
- CLAUDE.md: refresh the stale Stack / Test / Packaging sections — the repo now *has* a
  pyproject.toml, a pytest suite, CI, and an RPM spec; CLAUDE.md still says "none yet" for
  all of them. Also update the layout description (single script → src/ package layout).

**Risk:** None (docs only).

---

## Execution order & loop closure

| Order | Item | Cites | Budget | Why this position |
|---|---|---|---|---|
| 1 | R1 | SK-02 | 0.5h | Everything after depends on a truthful local test loop |
| 2 | R2 | SK-01, SK-04 | 3h | Only user-facing silent-wrong-answer path; tests first |
| 3 | R3 | SK-03 | 1h | One line, pinned by a new regression test from step 2's habits |
| 4 | R4 | SK-05, SK-06 | 4h | Builds on R2's contract; largest item, scope-cuttable |
| 5 | R5 | SK-07, SK-08 | 2h | Pipeline-only; enforces the release invariant before R6 |
| 6 | R6 | SK-10 | 3h | Depends on R5's honest CI |
| 7 | R7 | SK-09 | 0.5h | Anytime; zero risk |
| 8 | R8 | SK-11 | 1h | Anytime; zero risk |

Total budget: **15h**. Per Step 5 (loop closure), each item's completion is recorded in
`refactor-prs.md` as ✅ / 🔄 / ❌ with the originating finding re-checked (e.g. R3 closes only
when the global-RNG probe from the audit shows state is no longer clobbered). `/ssd verify`
re-runs codebase-skeptic on the identical scope afterward; findings not closed here will
resurface there.

**Not in scope (uncited by design):** vectorizing the sort-key loop (Wozniak explicitly said
leave it), fractional-proportion *support* (feature work, not refactor — belongs in a future
`/ssd feature` if wanted), PyPI rename (blocked on a naming decision only the maintainer can make).
