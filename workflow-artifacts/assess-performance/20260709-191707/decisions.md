# Decisions & assumptions - assess performance (colspan design)

## Concern / scope assessed
- Concern: **performance** (runtime/allocation of the render path).
- Scope narrowed by `$ARGUMENTS` to the colspan design in
  `.agents/plans/pending/20260709-colspan-support.md`. Assessed the *proposed* design
  against the *actual* hot paths in `src/vistab.py`; did not benchmark shipped code
  (colspan is not implemented yet), so findings are complexity/allocation arguments tied
  to specific source lines, plus the absence of measurement.

## Project conventions discovered
- Single-module pure-Python library + CLI (`src/vistab.py`, ~3528 lines). No DB/network;
  load is CPU + string allocation during formatting/rendering.
- No `GUIDING_PRINCIPLES.md` -> used universal fallback principles + `FUNCTIONAL_SPEC.md`
  backward-compat and streaming (§11) invariants.
- Plan lifecycle: `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
  IPD written under `pending/` per assess template naming (`YYYY-MM-DD-assess-performance.md`).
- Run record under `workflow-artifacts/assess-performance/<RUN_ID>/` (this dir).

## Key decisions
- **Verdict "adequate, with guardrails needed":** the object-grid design is not
  inherently super-linear; the risk is (a) doing per-row work per display line, (b) an
  unbounded F11 rule algorithm, and (c) shipping with no measurement. All are avoidable.
- **Fix-by-default, no deferrals:** every finding is Low Remediation Risk (the fixes
  reduce cost / add a small benchmark; none add architectural complexity). So all seven
  are proposed for action now.
- **Framed as guardrails on the colspan feature, not a separate build.** These
  requirements should be folded into colspan execution because they constrain that code.

## What was intentionally NOT proposed (and why)
- General speed rewrites of `_compute_cols_width`, `vislen`, or the wrapping engine:
  out of scope for the colspan concern and would be speculative micro-optimization
  (Complexity axis of the Fix Bar). The performance lens explicitly warns against
  optimizing where there is no evidence of real cost.
- Parallelism/concurrency: not applicable to a synchronous terminal renderer.

## Assumptions (flagged for human confirmation)
1. Acceptable no-span regression budget assumed at <= ~1.15x baseline render time.
2. Benchmark assumed to be a local pre/post check, not initially a CI gate.
3. `str(cell)` via the mandatory `VistabCell.__str__` (colspan plan §3.1) is the value
   accessor for width; assumed cheap but flagged P4 to compute width once.

## Open questions for the user
- Confirm the performance budget (Q1) and benchmark CI policy (Q2).
- Decide object-vs-tuple render representation (Q3) during colspan execution with the
  benchmark in hand.
