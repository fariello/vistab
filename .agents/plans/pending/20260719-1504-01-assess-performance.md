# IPD: Assess performance - render hot-path micro-optimizations (evidence-backed)

- Date: 2026-07-19
- Concern: performance (runtime/allocation of the render path)
- Scope: whole library render path in `src/vistab.py` (draw / _draw_line / _splitit /
  _compute_cols_width / _str / bidi gate). Assesses SHIPPED 1.2.1 code (supersedes the
  2026-07-09 assess-performance, which reviewed the colspan DESIGN before implementation).
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): /assess performance; proposed 4 changes.

## Goal

Keep vistab's render fast for real use without adding complexity. Assessment is grounded in an
actual cProfile run and a scaling sweep, not speculation. Headline result: the render is
**adequate** and scales **linearly** (~120-130 us/row, flat from 500 to 8000 rows), with no
algorithmic, I/O, network, or concurrency problem (it is a pure in-memory string builder). A
few small, profile-evidenced redundancies are worth removing; all are low risk.

## Project conventions discovered (Step 0)

- Guiding principles: none in repo; universal fallback (KISS is the operative one here: do not
  micro-optimize without evidence). Prose convention: no em/en dashes.
- Plan lifecycle: `.agents/plans/pending/`, `YYYYMMDD-HHMM-NN-<slug>.md`.
- Stack: single-module pure-Python library + CLI; dep wcwidth; no DB/network/threads.
- A `benchmarks/bench_render.py` exists (ad-hoc timing print), not a committed baseline.

## Evidence (measured, not guessed)

- cProfile, 3x render of a 1000x8 mixed table (max_width=120): 1.380s total. Cumulative
  hotspots: `_draw_line` (0.606s), `_splitit` (0.346s), `_compute_cols_width` (0.200s),
  `_str` (0.154s, 24000 calls), `_len_cell` (0.149s, 24024), `vislen` (0.084s, 51051),
  `_span_block_width` (0.080s, 48048), `wrap_list` (0.078s, 24024), `isinstance` (0.076s,
  472512 calls), `_infer_auto_dtypes` (0.073s).
- Scaling sweep (8 cols, mixed): 500->80ms, 1000->130ms, 2000->256ms, 4000->493ms,
  8000->963ms. Per-row cost is FLAT (~120-130 us) -> linear, no super-linear term.
- `StringLengthCalculator.len` is already `@lru_cache(maxsize=8192)` (per-string width memoized).
- `_str` rebuilds an 8-entry `format_map` dict on EVERY call; measured ~7.6ms per 1000x8x3
  render (~6% of that render) just constructing constant dicts.
- The 1.2.1 bidi gate scans every cell with a regex (`_contains_rtl`) on every `draw()` even
  for pure-ASCII tables (src/vistab.py:2263-2265 and the stream path 2394-2396).

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| P1 | Low | Low | engineer | allocation/repeated-work | `_str` rebuilds the constant `format_map` dict on every cell (24000 calls/render; ~6% of render time). It maps codes to bound methods and never varies per call. | src/vistab.py:2588-2600; profile `_str` 24000 calls |
| P2 | Low | Low | engineer | repeated-work | The bidi gate runs a per-cell regex scan (`_contains_rtl`) over the ENTIRE table on every draw, even when no cell is RTL and even when `set_bidi(False)`. For ASCII tables this is pure overhead added in 1.2.1. | src/vistab.py:2263-2265, 2394-2396 |
| P3 | Low | Low | engineer | repeated-work | `_get_spanned_boundaries` walks each row's cells to build a set even for tables with NO spans (called twice per interior hline). A table-level "has any span" fast path would skip it entirely in the common no-span case. | src/vistab.py:2671-2683, 2725-2726 |
| P4 | Medium | Low | architect/stakeholder | measurement | There is no committed performance baseline/benchmark that CI or a developer can run to PROVE an optimization helped or catch a regression. `benchmarks/bench_render.py` prints ad-hoc timings but asserts nothing and is not wired to anything. Without it, P1-P3 (and future changes) are unverifiable. | benchmarks/bench_render.py (no assertions/baseline) |

No Blocker/High findings. No quadratic paths, no I/O/network/concurrency issues.

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | P4 | Establish a small, deterministic micro-benchmark (extend `benchmarks/bench_render.py` or add a `benchmarks/baseline.py`) that renders fixed sizes and reports us/row, so P1-P3 can be measured before/after. Do NOT gate CI on absolute timings (machine-variance); it is a developer tool + optional informational check. | benchmarks/ | Low | Running it prints stable us/row for fixed inputs; used as the before/after harness for steps 2-4. |
| 2 | P1 | Hoist the `format_map` to a class/module-level constant (built once), keyed to the bound methods via `getattr(self, ...)` or a static map resolved in `_str`. Output must be byte-identical. | src/vistab.py:2579-2600 | Low | Full suite byte-identical (146+ tests, fixtures unchanged); benchmark shows a small render speedup. |
| 3 | P3 | Compute a table-level `_has_spans` flag once per draw (from the already-known cell metadata) and short-circuit `_get_spanned_boundaries` (return the empty set) when false. Byte-identical for both spanned and unspanned tables. | src/vistab.py:2671-2683 and the hline callers | Low | Colspan fixtures + non-span fixtures byte-identical; benchmark shows reduced calls for no-span tables. |
| 4 | P2 | Skip the per-cell RTL regex scan when `self._bidi` is False, and short-circuit the scan on the first RTL hit (it already uses `any(...)`, but confirm it stops early and is not run when bidi is disabled). Optionally reuse the single pass rather than scanning header and body separately. Output byte-identical (isolates only added when RTL present, unchanged). | src/vistab.py:2263-2265, 2394-2396 | Low | RTL tests unchanged (isolates still present for RTL); ASCII render with `set_bidi(False)` does zero RTL scanning; benchmark shows ASCII render is no slower than pre-1.2.1 baseline. |

## Deferred / out of scope (with reason)

None deferred. All four are Low Remediation Risk. Explicitly NOT proposed (see scope check):
no C-extension, no caching of whole rendered rows, no threading, no algorithmic rewrite: there
is no evidence of cost that would justify that complexity.

## Scope check

- Over-scope: rejected speculative micro-opts (e.g. replacing all `isinstance` checks, rewriting
  the wrap engine). The 472k `isinstance` calls look large but are cheap and spread; no single
  hot quadratic. Optimizing them would add complexity for unmeasured gain (Complexity axis).
- Under-scope: the missing benchmark baseline (P4) is the real gap; proposed first so the rest
  is provable.

## Required tests / validation

- Byte-identical output guarantee: the FULL existing suite (unit + regression fixtures) must
  stay green and unchanged after steps 2-4 (these are pure internal optimizations; any fixture
  diff is a regression, not an improvement).
- The benchmark (step 1) run before and after steps 2-4, reporting us/row for fixed 1000x8 and
  a colspan and an RTL case, to show the intended reduction without absolute-time CI gating.
- `python -m pytest` / `unittest discover` green; no em/en dashes introduced.

## Spec / documentation sync

None: these are internal performance changes with byte-identical output. No public API, CLI,
or rendered-output change. (If P4 adds a documented `make bench`-style entry point, note it in
CONTRIBUTING.)

## Open questions

- P4: should the benchmark be purely a local developer tool, or an informational (non-gating)
  CI job? Recommend local tool + optional non-gating CI, since GitHub runners are too noisy for
  absolute-time assertions. Confirm.
- Priority: is render speed a real user pain today (e.g. very large tables in a hot loop), or is
  this pre-emptive hygiene? The measured cost is modest (~130 us/row); if no user is hurting,
  P1-P4 are low-priority polish and could wait. The plan is safe either way.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution; it is NOT
auto-executed.

1. Review (optionally `/plan-review`, which sets `Status: reviewed`); update `Status:`
   (`to-review` -> `reviewed` -> `approved`) with a Workflow-history line at each step.
2. On approval, set `Status: approved` (+ `Approval:` line), implement in order (benchmark
   first), verify byte-identical output + measured improvement.
3. Then set the terminal `Status:` and `git mv` this IPD from `.agents/plans/pending/` to
   `.agents/plans/executed/`.
