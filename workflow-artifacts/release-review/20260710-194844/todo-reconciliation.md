# TODO / Backlog Reconciliation (full triage — Section 5)

Sole backlog source: `TODO.md`. No in-code TODO/FIXME markers.

| # | Item | Classification | Rationale |
|---|---|---|---|
| 1 | Jagged-row routing (`on_jagged_row = error/expand/truncate/merge`) — future mechanism | out-of-scope-for-release | Design exploration; current `on_short_row`/`on_long_row` already handle jagged rows. Not promised as shipped. |
| 2 | Colspan | stale/done (accurate) | Marked "Completed in v1.2.0"; matches code, tests, docs. TODO.md is honest. |
| 3 | Rowspan | out-of-scope-for-release | Explicitly deferred with clear architecture rationale (would need a 2D canvas rewrite). Correctly labeled future. |
| 4 | Auto-align plain rows under spans | out-of-scope-for-release | Deferred with rationale (ambiguity + grid-invariant risk); recorded during colspan work. |
| 5 | CLI `--delimiter` | out-of-scope-for-release | Future ergonomics; not promised as existing. Verified absent from code+docs (no contradiction). |
| 6 | CLI `--auto-width` | out-of-scope-for-release | Future ergonomics. Absent from code+docs. |
| 7 | CLI `--json-out` | out-of-scope-for-release | Future feature. Absent from code+docs. |

**No `must-before-release` or `should-before-release` TODO items.** TODO.md is honest and
does not contradict the docs. Only release-relevant reconciliation note: TODO.md says
"Colspan Completed in v1.2.0" while the package version is still 1.1.3 → reinforces
S1-BUG1 (version bump needed).
