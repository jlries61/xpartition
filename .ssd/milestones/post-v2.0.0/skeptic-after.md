---
skill: codebase-skeptic
version: 1.4.0
produced_at: 2026-07-09T15:55:00-07:00
produced_by: claude-fable-5
project: xpartition
scope: SHA fac93f4 + branch milestone/post-v2.0.0 (10 commits) — identical file scope to skeptic-before.md
consumed_by: [refactor, code-reviewer, ssd]
finding_counts:
  structural_risk: 0
  problem: 0
  concern: 2
findings:
  - id: SK-01
    severity: problem
    status: closed
  - id: SK-02
    severity: problem
    status: closed
  - id: SK-03
    severity: problem
    status: closed
  - id: SK-04
    severity: concern
    status: closed
  - id: SK-05
    severity: concern
    status: closed
  - id: SK-06
    severity: concern
    status: closed
  - id: SK-07
    severity: concern
    status: closed
  - id: SK-08
    severity: concern
    status: closed
  - id: SK-09
    severity: concern
    status: closed
  - id: SK-10
    severity: concern
    status: partial
  - id: SK-11
    severity: concern
    status: closed
  - id: SK-12
    severity: concern
    status: new
    title: Release workflow runtime-unverified until a throwaway-tag drill
  - id: SK-13
    severity: concern
    status: new
    title: Indicator name colliding with an existing column silently overwrites it (pre-existing, surfaced in review)
voices_activated: [fowler, uncle-bob, beck, humble, jobs, wozniak]
posture: sound
gate_pass: true
---

# Codebase Review (verification pass): `xpartition`

**Reviewed:** 2026-07-09, branch `milestone/post-v2.0.0` at `7114495`
**Scope:** identical to skeptic-before.md
**Method:** every original finding re-checked by executing the failure path it described, not by
reading the diff. Probes: all seven invalid-input classes raise `ValueError`; 0.8/0.2 → exact
80/20; 1/3–2/3 → 34/66; global RNG state bit-identical before/after a call; stratified balance
intact; suite 38 passed; coverage 94% measured against `src/`.

## Finding dispositions

| ID | Before | After | Evidence |
|---|---|---|---|
| SK-01 | 🔴 silent wrong partition | ✅ closed | Everyday fractions now normalize exactly (80/20 verified); unrealizable precision raises; oversized-cycle guard added after round-1 review caught the reintroduction |
| SK-02 | 🔴 tests test installed copy | ✅ closed | Coverage now cites `src/`; CLI subprocess probed to resolve `src/xpartition` |
| SK-03 | 🔴 global RNG clobbered | ✅ closed | State-isolation probe green; assignments pinned bit-for-bit |
| SK-04 | ⚠ no validation | ✅ closed | zero/negative/inf/fractional-cv/empty-indicators all raise (probed) |
| SK-05 | ⚠ traceback UX | ✅ closed | bad numerics, unreadable files, unknown options, unknown --by fields: clean two-line errors |
| SK-06 | ⚠ dead code / getopt | ✅ closed | argparse; `ncv` and `COMMA` gone |
| SK-07 | ⚠ CI matrix dishonest | ✅ closed | 3.9/3.13/3.14; floor raised to 3.9 |
| SK-08 | ⚠ version drift risk | ✅ closed | version-check CI job; logic verified both directions |
| SK-09 | ⚠ tree hygiene | ✅ closed | no untracked noise; nothing deleted |
| SK-10 | ⚠ no release channel | 🔄 partial | Workflow exists and parses; **not yet exercised** — see SK-12 |
| SK-11 | ⚠ doc drift | ✅ closed | README + CLAUDE.md verified against reality |

**New findings (🆕):**

- **SK-12 (⚠, successor to SK-10's residue):** `.github/workflows/release.yml` has never run.
  Until a throwaway tag exercises it end-to-end, the next release depends on unproven automation —
  Humble's "release theatre" risk in mild form. One drill closes it.
- **SK-13 (⚠, pre-existing, newly surfaced):** an indicator name that matches an existing column
  silently overwrites that column (`indicators=["X"]` destroys data column X; re-running on
  already-partitioned output silently refreshes SAMPLE). Possibly intentional; needs a maintainer
  decision — document as a feature or reject the collision.

No 🆕 finding is BLOCKER/🔴 severity. No regression found in behavior for valid inputs: the
pinned-seed test and all 15 original behavior tests pass unchanged.

## Posture

```
✅ Sound — improved
```

The dominant failure mode from the before-audit ("trust at the boundaries, failing silently") is
substantively closed: every identified silent-failure path now fails loudly, the local feedback
loop tests the code being edited, and the release invariants are machine-checked. Remaining
concerns are operational follow-ups, not code defects.

## Hook for `/code-reviewer` (updated)

| Finding | Files/patterns | Trigger for code-reviewer |
|---|---|---|
| SK-12 release drill | `.github/workflows/release.yml` | First `v*` tag: confirm the workflow ran and attached artifacts before announcing |
| SK-13 indicator collision | `src/xpartition/__init__.py` | Any PR touching indicator handling: force the collision decision |
| Cycle guard | `src/xpartition/__init__.py` | Any PR touching `_normalize_counts` or the assignment loop: re-probe high-precision fractions on a small frame |
