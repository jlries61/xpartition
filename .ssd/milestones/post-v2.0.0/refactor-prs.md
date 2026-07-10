# Refactor closure record — milestone post-v2.0.0

Branch: `milestone/post-v2.0.0` (10 commits, not yet pushed — one branch of small
independently-revertable commits rather than separate PRs, since all items were executed in a
single supervised session; the commit granularity preserves the per-item rollback property).

| Item | Cites | Commit | Closure | Re-check of originating finding |
|---|---|---|---|---|
| R1 | SK-02 | 1994a3f | ✅ closed | Coverage cites `src/…` paths; CLI subprocess resolves `src/xpartition` (probed) |
| R2 | SK-01, SK-04 | 8d75460 + cc68170 | ✅ closed | 0.8/0.2 → exact 80/20 (was 100% Learn); zero/negative/inf inputs raise; contract revised mid-flight per maintainer to normalize fractions instead of rejecting |
| R3 | SK-03 | 985c432 | ✅ closed | Audit's global-RNG probe re-run as a test: state no longer clobbered; assignments bit-for-bit unchanged (pinned) |
| R4 | SK-05, SK-06 | 2adcf43 | ✅ closed | `--cv=ten`, unreadable file, unknown option, unknown `--by` field: all clean two-line errors; `ncv`/getopt/COMMA gone |
| R5 | SK-07, SK-08 | a67a04d | ✅ closed | Matrix 3.9/3.13/3.14; floor 3.9; version-check grep verified in both directions locally |
| R6 | SK-10 | 5149bae | 🔄 partial | Workflow written and YAML-validated; **runtime unverified until a throwaway tag is pushed** — do this before the next real release |
| R7 | SK-09 | f2b4834 | ✅ closed | `git status` shows no untracked noise; nothing deleted |
| R8 | SK-11 | e451f46 | ✅ closed | README typos fixed; CLAUDE.md matches post-2.0 reality |
| R9 (round-1 review findings) | MAJOR-1, MINOR-1/2/3, NIT-1 | 7114495 | ✅ closed | Cycle-longer-than-table now raises; see code-review.md round 2 |

Budget: 15h planned; actual wall-clock well under (single session). No item hit the 150%
scope-reconsider threshold.

Residue (explicitly named):
- **R6:** the release workflow needs one throwaway-tag drill (`git tag v2.0.1-rc1 && git push origin v2.0.1-rc1` on a test basis, then delete) before trust.
- **QUESTION-1 (code-review):** indicator name colliding with an existing column silently
  overwrites it (pre-existing). Maintainer decision wanted: document as re-partitioning feature,
  or reject.
- **Deferred by design:** PyPI rename (blocked on naming decision), sort-key vectorization
  (explicitly declined by audit), fractional-support README example expansion beyond the one
  sentence added in R8.
