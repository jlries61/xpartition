# Milestone post-v2.0.0 — Verification

**Date:** 2026-07-09 · **Branch:** `milestone/post-v2.0.0` at `7114495` (10 commits over `fac93f4`)

## Pass criteria (per /ssd verify)

| Criterion | Result |
|---|---|
| All original 🔴 findings (SK-01, SK-02, SK-03) ✅ closed | ✅ — each re-verified by executing the original failure path (see skeptic-after.md) |
| No 🆕 new-regression at BLOCKER severity | ✅ — two new ⚠ concerns (SK-12 release drill, SK-13 indicator collision), neither blocking |
| Code review on remediation diff has no BLOCKERs | ✅ — code-review.md: round 1 found 1 MAJOR (fixed as R9), round 2 gate_pass: true; 0 BLOCKERs in either round |

**VERIFICATION: PASS** — the milestone is complete pending the two operational follow-ups below.

## Metrics delta

| Metric | Before | After |
|---|---|---|
| Tests | 15 | 38 |
| Coverage | 87% (measured against the wrong tree — installed copy) | 94% (measured against `src/`) |
| Silent-wrong-output paths | ≥4 known (fractional, all-zero, oversized-cycle, RNG side effect) | 0 known — all raise `ValueError` |
| CI jobs | test (3.9/3.13) + build | test (3.9/3.13/3.14) + build + wheel smoke-test + version-check |
| Release artifacts | none | tag-triggered GitHub Release (sdist+wheel) — pending first drill |

## Worth knowing

- Round 1 of the gate **failed**: the fraction-normalization fix itself reintroduced the SK-01 bug
  class for high-precision inputs (0.123457/0.876543 → silent 100% Learn). Caught by the
  review's fix-introduces-edge-cases pass, fixed in R9, re-gated clean. The milestone's central
  lesson stands: this codebase's failure mode is silent wrongness at input boundaries — every
  future change to `_normalize_counts` or the assignment loop should re-probe a small frame with
  precise fractions (hook recorded in skeptic-after.md).
- Contract decision (maintainer, mid-milestone): fractional sizes are **normalized** to the
  smallest whole-number cycle, not rejected. Unrealizable precision (cycle > table) is rejected.

## Deploy status & follow-ups (not blockers)

1. Branch is local; **not pushed**. To ship: push, open PR, let CI run (its first run exercises the
   new matrix, wheel smoke-test, and version-check jobs), merge, then tag per RELEASING.md.
2. **SK-12:** before the next real release, drill `release.yml` with a throwaway tag.
3. **SK-13:** decide indicator-collision semantics (document or reject).
