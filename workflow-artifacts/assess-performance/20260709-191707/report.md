# Assessment run report - performance (colspan design)

- Date / run ID: 20260709-191707
- Concern: performance
- Scope: The colspan design in `.agents/plans/pending/20260709-colspan-support.md`, assessed against the render hot paths in `src/vistab.py`.
- IPD written: `.agents/plans/pending/2026-07-09-assess-performance.md`
- Verdict: **adequate, with guardrails needed** for performance — the design is not inherently slow, but it adds work to the one hot path and ships no measurement, so it is at risk of an unproven regression without the proposed guardrails.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| P1 | High | Low | Software engineer | `_draw_line` could recompute span block width/boundaries per wrapped display line (inner `for i in range(...)` at [vistab.py:2517](file:///home/gfariello/VC/vistab/src/vistab.py)) instead of once per row -> O(lines x cols). |
| P2 | High | Low | Architect | §3.9a (F11) horizontal-rule junction suppression has no complexity bound; a naive per-rule full-row scan is O(rows^2 x cols) per `draw()`. Must precompute once, O(cells). |
| P3 | Medium | Low | Software engineer | §3.6 allocates a new `VistabCell` per cell per render on top of ingestion-time objects -> M x N alloc churn per render. |
| P4 | Medium | Low | Software engineer | §3.5/§3.1a call `_len_cell(str(cell))`; risk of repeated `str()` allocation and cache-adjacent work in front of the LRU-cached `vislen`. |
| P5 | Medium | Low | Power user / stakeholder | `stream()` uses bounded-sample geometry; a wide post-sample `ColSpan` either mis-sizes or tempts mid-stream width recompute (would break the O(1)/row streaming contract, `FUNCTIONAL_SPEC.md` §11). |
| P6 | Medium | Low | Architect / QA | No rendering benchmark exists; "no regression" is currently unprovable. |
| P7 | Low | Low | Software engineer | `_span_block_width` list-slice allocation is negligible unless on the per-line path (compounds with P1). |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. Add a dependency-free rendering benchmark; capture a baseline on `main` before colspan (P6).
2. Compute span block geometry once per row in `_draw_line`, not per display line; avoid slice alloc on the per-line path (P1, P7).
3. Precompute the F11 suppressed-boundary set once per `draw()` in an O(cells) pass; forbid per-rule full-table scans (P2).
4. Cap render-time cell allocation to one per cell per render (or carry light tuples) (P3).
5. Compute each source cell's content width once during the width pass; keep `vislen` on its cached path (P4).
6. Make the streaming rule explicit: keep sample geometry, wrap/clip post-sample spans, no mid-stream width recompute; document in `FUNCTIONAL_SPEC.md` §11 (P5).
7. Add a performance line to the colspan Definition of Done, backed by the benchmark (all).

## Deferred (with reason)

- None. All findings are Low Remediation Risk and proposed for action now.

## Out-of-repo / organizational notes (if any)

- None. All actions are in-repo (source + benchmark + spec).

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before
execution. This workflow does not execute the plan. In practice these seven guardrails
should be folded into the colspan implementation work, since they constrain that feature.
