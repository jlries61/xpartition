---
skill: code-reviewer
version: 1.7.0
produced_at: 2026-07-09T15:20:00-07:00
produced_by: claude-fable-5
project: xpartition
scope: milestone/post-v2.0.0 (master..HEAD, commits R1–R8)
consumed_by: [ssd]
finding_counts:
  blocker: 0
  major: 0
  minor: 0
  question: 1
  suggestion: 1
  nit: 0
gate_pass: true
remediation_mode: true
round: 2
closed_from_previous_round: [MAJOR-1, MINOR-1, MINOR-2, MINOR-3, NIT-1]
---

# Code Review — milestone/post-v2.0.0 remediation branch (round 1)

**Scope:** 9 commits (R1–R8) closing skeptic findings SK-01…SK-11.
**Verdict:** One MAJOR — the fraction-normalization fix reintroduces the silent-wrong-partition
bug class it was meant to close, for high-precision inputs. Gate FAILS; return to coder.
All findings below were verified by executing the code, not by inspection alone.

## Phase 1.5 — Prior-finding follow-up (SK-01…SK-11)

| Finding | Claim | Verified status |
|---|---|---|
| SK-01 silent wrong partition | R2 + R2(rev) | 🔄 **partially** — everyday fractions (0.8/0.2, 1/3) fixed and tested; high-precision fractions still silently degenerate (see MAJOR-1) |
| SK-02 tests hit installed copy | R1 | ✅ addressed — verified: in-process imports and CLI subprocess both resolve to `src/` |
| SK-03 global RNG clobbered | R3 | ✅ addressed — isolation test + pinned-assignment regression both green; assignments bit-for-bit unchanged |
| SK-04 no input validation | R2 | ✅ addressed — negative/zero/empty-indicator paths raise; tests cover each |
| SK-05 traceback error UX | R4 | 🔄 **partially** — numeric options, unknown options, unreadable files now clean; `--by=<typo>` still dumps a raw KeyError traceback (MINOR-2) |
| SK-06 dead code / getopt | R4 | ✅ addressed — `ncv` gone, argparse in, USAGE/docstring aligned |
| SK-07 CI matrix honesty | R5 | ✅ addressed — floor 3.9 (also required by new `math.lcm`), 3.14 added |
| SK-08 version drift | R5 | ✅ addressed — version-check job; grep logic verified in both directions |
| SK-09 working-tree hygiene | R7 | ✅ addressed — nothing deleted, all advertised paths now ignored |
| SK-10 no release artifacts | R6 | ✅ addressed in code — workflow **unverified until a throwaway tag run** (deploy-path caveat carried in commit message and plan) |
| SK-11 doc drift | R8 | ✅ addressed — README typos fixed, CLAUDE.md rewritten to post-2.0 reality |

No silent findings — every SK item was touched and accounted for.

## Findings

### 🟠 MAJOR-1 — Normalization reintroduces silent degenerate partitions when the cycle exceeds the table
`src/xpartition/__init__.py` (`_normalize_counts` + assignment loop)

Verified: `xpartition(df100, nlearn=0.123457, ntest=0.876543)` → **100% "Learn", no error** —
exactly the SK-01 failure class this branch exists to kill. `limit_denominator(10**6)` faithfully
preserves high-precision fractions, producing a normalized cycle (here 123457:876543, length 10⁶)
longer than the table; the positional assignment then never leaves the Learn segment. Plausible in
programmatic use (proportions computed from data, e.g. `37/300` to six decimals). The same
degeneracy exists for raw integer inputs (`nlearn=200, ntest=300` on 100 rows — pre-existing), but
the fraction feature makes it much easier to hit accidentally.

**Required fix:** after normalization, if the assignment-cycle length exceeds the number of rows
(sample mode), raise `ValueError` telling the user the table is too small for the requested
precision. Symmetrically, `cv > nrows` should also be rejected. This is loud-failure, consistent
with the milestone's decided contract.

### 🟡 MINOR-1 — `inf` escapes the input guards as an uncaught `OverflowError`
`src/xpartition/__init__.py` (`_normalize_counts`)

Verified: `Fraction(float("inf"))` raises `OverflowError`, which the `except (TypeError,
ValueError)` does not catch; the CLI's `_nonneg_number` happily passes `--nlearn=inf` through
(`float("inf") >= 0`), so the user gets a traceback. Add `OverflowError` to the except tuple.

### 🟡 MINOR-2 — `--by` with a nonexistent field dumps a raw pandas KeyError traceback
`src/xpartition/cli.py`

Verified: `--by=NOSUCH` → multi-screen traceback. A typo'd field name is an everyday user error —
the exact SK-05 class. Validate the `by` and `indicators` fields (or catch `KeyError`) in the CLI
and report which fields are missing, exit 2.

### 🟡 MINOR-3 — CI no longer tests the installed package anywhere
`.github/workflows/ci.yml`, `pyproject.toml`

Side effect of R1: `pythonpath=["src"]` + subprocess `PYTHONPATH=src` mean even CI's pytest now
exercises the checkout, not the wheel it installed. A packaging defect (module missing from the
wheel) would pass tests and `twine check`. Suggest one CI step that runs the suite (or at least an
import + CLI smoke) against the installed distribution with `src/` masked.

### 💭 QUESTION-1 — Indicator name colliding with an existing column silently overwrites it
Pre-existing behavior, unchanged by this branch: `xpartition(df, indicators=["X"])` replaces data
column `X` with assignments; re-running on already-partitioned output silently refreshes `SAMPLE`.
Possibly intentional (re-partitioning). Decide and document; not gate-relevant.

### 💡 SUGGESTION-1 — Document the snap-to-zero behavior of sub-microscopic sizes
`nlearn=1e-9` snaps to 0 via `limit_denominator` (verified: all rows became Test). Defensible, but
one docstring sentence ("sizes below 5×10⁻⁷ of the total are treated as 0") would make it a
contract instead of a surprise. Largely mooted if MAJOR-1's cycle-vs-rows check lands.

### 📝 NIT (summarized)
`--by=` / `--indicators=` (empty value) produce `[""]` — a nonsense field name that will surface
as the MINOR-2 traceback today; the MINOR-2 fix should treat empty names as "not provided" or
reject them.

## Phase 3.5 sweep (fix-introduces-edge-cases)
The new defensive surfaces were each probed: guard clauses (MAJOR-1, MINOR-1 found), CLI
try/excepts (`OSError, ValueError` coverage confirmed adequate for read_csv: ParserError,
EmptyDataError, UnicodeDecodeError all subclass ValueError; FileNotFoundError subclasses OSError),
cv-override warning (correct: fires only when flags explicitly given, exit 0), version-check grep
(verified both match and mismatch directions), release workflow (YAML parses; tag↔version guard
present; **runtime unverified** — needs the throwaway-tag drill before the next release).

## Gate decision (round 1)
`blocker == 0` but `major == 1` → gate FAILED. Returned to coder for MAJOR-1 (required)
and MINOR-1/2/3.

---

## Round 2 (inline update) — remediation commit R9 (`7114495`)

Each closure verified against the code and by execution, not from the commit message:

- **MAJOR-1 ✅ closed.** Re-probed: `nlearn=0.123457, ntest=0.876543` on 100 rows now raises
  `ValueError` ("assignment cycle of 1000000 records, but the table has only 100"); `cv=101` on
  100 rows raises symmetrically. Empty frames verified exempt (`test_empty_frame_still_partitions`).
  Pleasant corollary: reducible oversized integer ratios (200:300) now normalize to 2:3 and
  partition correctly (pinned by `test_reducible_integer_ratio_normalized`) — the pre-existing
  integer degeneracy is fixed for the reducible case and loud for the coprime case (199:301 raises).
- **MINOR-1 ✅ closed.** `OverflowError` added to the guard's except tuple; `nlearn=inf` now raises
  a clean `ValueError` (re-probed).
- **MINOR-2 ✅ closed.** `--by=NOSUCH` exits 2 with "field(s) not in the input: NOSUCH", no
  traceback (`test_cli_unknown_by_field` green).
- **MINOR-3 ✅ closed.** CI build job gained a wheel smoke-test (install the wheel, run the CLI and
  an import from /tmp with the checkout masked); YAML validated.
- **NIT-1 ✅ closed.** Empty comma-list tokens discarded; `--indicators=` now reaches the library's
  empty-indicators guard and exits cleanly.
- **QUESTION-1 / SUGGESTION-1 → open, non-gating.** Indicator-collision overwrite is pre-existing
  and needs a maintainer decision; the snap-to-zero note was added to the docstring (SUGGESTION-1
  is thereby addressed in substance, left listed for the verify pass to confirm).

Full suite: **38 passed**. `blocker == 0 AND major == 0` → **gate_pass: true**.
