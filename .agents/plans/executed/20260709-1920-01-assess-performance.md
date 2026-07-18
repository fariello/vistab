# IPD: Assess performance - Colspan support design (performance guardrails)

- Date: 2026-07-09
- Concern: performance
- Scope: The proposed colspan design in `.agents/plans/pending/20260709-colspan-support.md`, assessed against the real render hot paths in `src/vistab.py`. This is a performance review of a *pending* design, not of shipped code.
- Status: EXECUTED / CLOSED (performance assessment informed the shipped colspan design). Status corrected 2026-07-11 during release-review 20260711-181922 (stale PENDING line on an executed/-located assessment).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Plan-review note (revisions applied):** This IPD was reviewed pre-execution and the
> `file:line` claims re-verified against `src/vistab.py`. Five findings (R1-R5) were added
> and fixed in place. The most important is R1: `draw()` memoizes `self._width` and does
> not clear it, so the benchmark must measure a **cold** path (fresh object per render) or
> it will hide the width-computation cost this plan cares about. Also fixed: the
> byte-identical gate now defers to the colspan plan's DoD instead of duplicating it (R2),
> the allocation acceptance criterion is now measurable via `tracemalloc` or reframed as
> time (R3), and the CI/`pytest`-collection ambiguities are resolved (R4, R5).

## Goal

Ensure the colspan feature ships without regressing Vistab's rendering performance, and
that its cost scales linearly with table size. Vistab is a terminal table renderer whose
one hot path is "format cells -> compute widths -> wrap -> draw lines," executed on every
`draw()` and per output line in `stream()`. The colspan design adds cell objects and new
per-cell/per-line work into exactly that path. This plan adds concrete performance
guardrails and a benchmark so the colspan implementation can be *proven* not to regress,
rather than assumed safe.

This IPD is a companion to the colspan IPD; it does not restate the feature. It adds
performance-specific requirements the colspan implementer (and its reviewer) must satisfy.

## Project conventions discovered (Step 0)

- **Project intent / stack:** `Vistab` is a single-module (`src/vistab.py`, ~3.5k lines)
  pure-Python terminal table library + CLI. No DB, no network; the "load" is CPU/allocation
  during string formatting and rendering (`FUNCTIONAL_SPEC.md` §1, §6). Streaming
  (`stream()`) is explicitly a memory-bounded path (`FUNCTIONAL_SPEC.md` §11).
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`/`PRINCIPLES.md` present; used the
  universal fallback (intuitive/self-documenting, general-case/configurable, KISS, honest
  docs) plus the `FUNCTIONAL_SPEC.md` backward-compatibility invariant (§5).
- **Pending-plans location/format used:** `.agents/plans/pending/`, files
  `YYYYMMDD-<slug>.md` (existing colspan plan follows this; this assessment file follows
  the assess template's `YYYY-MM-DD-assess-<concern>.md` naming).
- **Contributor/spec-sync contract:** `AGENTS.md` (workflow index only; no extra plan
  rules). Behavior-visible changes should sync `FUNCTIONAL_SPEC.md`/`docs/`.
- **Relevant hot-path facts verified in source:**
  - `StringLengthCalculator.len` is `@lru_cache(maxsize=8192)` ([src/vistab.py:224](file:///home/gfariello/VC/vistab/src/vistab.py)); `vislen` dispatches to it for str/bytes ([src/vistab.py:892](file:///home/gfariello/VC/vistab/src/vistab.py)). Visible-length is already memoized; new code must not defeat this cache.
  - Per `draw()`: `_str` runs once per cell ([src/vistab.py:1880-1885](file:///home/gfariello/VC/vistab/src/vistab.py)); `_draw_line` -> `_splitit` runs once per row, then an inner `for i in range(self.vislen(line[0]))` renders each wrapped display line ([src/vistab.py:2517](file:///home/gfariello/VC/vistab/src/vistab.py)).
  - `_build_hline` runs once per row-gap and reads only `self._width` today ([src/vistab.py:2219-2248](file:///home/gfariello/VC/vistab/src/vistab.py)); it has no per-row context.
  - `_compute_cols_width` is O(rows x cols) and memoizes via `if hasattr(self, "_width"): return` ([src/vistab.py:2292](file:///home/gfariello/VC/vistab/src/vistab.py)).
  - `stream()` computes geometry once from a bounded sample (default 100 rows) and reuses it ([src/vistab.py:1934-1983](file:///home/gfariello/VC/vistab/src/vistab.py)); it must not trigger width recomputation per streamed row.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate for acting now.
"Colspan plan" = `.agents/plans/pending/20260709-colspan-support.md`.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| P1 | High | Low | Software engineer | Hot-path recomputation | Colspan plan §3.9 computes `_span_block_width` while iterating columns *inside* `_draw_line`. `_draw_line` re-renders every wrapped display line via `for i in range(...)` ([src/vistab.py:2517](file:///home/gfariello/VC/vistab/src/vistab.py)). If block widths/boundaries are recomputed per display line (not once per row), rendering becomes O(lines x cols) with redundant work per tall/wrapped row. | colspan plan §3.9; [src/vistab.py:2517-2523](file:///home/gfariello/VC/vistab/src/vistab.py) |
| P2 | High | Low | Architect | Algorithmic complexity | Colspan plan §3.9a (F11) horizontal-rule junction suppression has no complexity bound. A naive "for each rule, scan all rows to find spans crossing each boundary" is O(rows^2 x cols) across a full `draw()` (a rule per gap x scanning all rows each time). Must be O(cells) precompute once. | colspan plan §3.9a; [src/vistab.py:2219-2248](file:///home/gfariello/VC/vistab/src/vistab.py), draw loop [src/vistab.py:1906-1910](file:///home/gfariello/VC/vistab/src/vistab.py) |
| P3 | Medium | Low | Software engineer | Allocation churn | Colspan plan §3.6 re-wraps every formatted cell into a *new* `VistabCell` on every `draw()`/`stream()` render, on top of ingestion-time objects (§3.2). That is M x N fresh objects per render plus attribute copies, added to a path that previously produced plain strings. For large/streamed tables this is measurable GC/alloc churn. | colspan plan §3.2, §3.6 |
| P4 | Medium | Low | Software engineer | Cache defeat | Colspan plan §3.5 / §3.1a call `self._len_cell(str(cell))`. `str(cell)` allocates a new string each call, and `_len_cell` splits on `\n`/`\t` then calls `vislen` per part. If `str(cell)` produces a distinct object each time or is called repeatedly per render, it adds work in front of the LRU-cached `len`. Content width per source cell should be computed once, not per width-pass iteration. | colspan plan §3.5; `_len_cell` [src/vistab.py:2250-2266](file:///home/gfariello/VC/vistab/src/vistab.py); `len` cache [src/vistab.py:224](file:///home/gfariello/VC/vistab/src/vistab.py) |
| P5 | Medium | Low | Power user / stakeholder | Scaling under streaming | `stream()` derives geometry from a bounded sample and reuses it ([src/vistab.py:1934-1983](file:///home/gfariello/VC/vistab/src/vistab.py)). A `ColSpan` whose wide content appears only *after* the sample either (a) is silently mis-sized (correctness) or (b) tempts an implementer to recompute widths mid-stream, which would make streaming O(n^2) and break its memory-bounded contract (`FUNCTIONAL_SPEC.md` §11). The design must pick "keep sample geometry, accept clip/wrap" and forbid mid-stream width recompute. | colspan plan §3.5/§3.8; [src/vistab.py:1983](file:///home/gfariello/VC/vistab/src/vistab.py); `FUNCTIONAL_SPEC.md` §11 |
| P6 | Medium | Low | Architect / QA | No measurement | Neither the repo nor the colspan plan has a rendering benchmark. Per the performance lens, optimizations/guarantees must be validatable. Without a baseline, "colspan didn't regress performance" is unprovable. | repo has no `benchmarks/`; colspan plan §4 (functional tests only) |
| P7 | Low | Low | Software engineer | Micro-alloc | `_span_block_width` sums a list slice `self._width[start:start+colspan]` (colspan plan §3.0); slicing allocates a temporary list. Negligible for small colspans, but if called per display line (see P1) it compounds. Prefer summing without slicing if it is on the per-line path. | colspan plan §3.0 |
| R1 | High | Low | Testing/QA | Benchmark validity | (Found during plan-review of this IPD.) `draw()` memoizes `self._width` and does NOT clear it in `finally` (only `_header/_rows/_row_size` are restored). A benchmark that reuses one `Vistab` object across iterations measures **warm** renders and hides width-computation cost — the very cost Step 5 targets — making the whole benchmark misleading. Must measure cold (fresh object) and warm separately. | [src/vistab.py:1875-1918](file:///home/gfariello/VC/vistab/src/vistab.py); memoization guard [src/vistab.py:2292](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R2 | Medium | Low | Architect | Test ownership | (Plan-review.) The "byte-identical no-span output" regression gate was stated here as if this IPD owns it, but the colspan plan already owns it (§0.3 item 1). Two owners risk divergent golden files. Make it a dependency, not a duplicate. | this IPD "Required tests"; colspan plan §0.3 |
| R3 | Medium | Low | Software engineer | Unmeasurable criterion | (Plan-review.) Step 4 asserted "no super-linear allocation growth" but Step 1 only measures time (`perf_counter`), so the allocation criterion was unvalidatable. Either measure with `tracemalloc` or reframe as time-proxied. | this IPD Step 1/Step 4 |
| R4 | Low | Low | QA | Internal inconsistency | (Plan-review.) Step 1 said "Runs in CI or locally" while Open Q2 leaves CI undecided. Aligned to the stated assumption (local pre/post; CI deferred to the human). | this IPD Step 1 vs Open Q2 |
| R5 | Low | Low | Testing/QA | Suite hygiene | (Plan-review.) A committed `benchmarks/` dir could be collected by `pytest` or slow the suite. Must be opt-in and excluded from default test discovery. | this IPD Step 1; `tests/` layout |

## Proposed changes (ordered, validatable)

These are additions to the colspan implementation's requirements. Fix-by-default; all are
Low Remediation Risk (they reduce complexity/cost, do not add architectural burden).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | P6, R1, R5 | Add a minimal, dependency-free rendering benchmark (`benchmarks/bench_render.py` using `time.perf_counter`, optionally `tracemalloc` for allocation) that renders representative tables (e.g. 1k and 10k rows x 8 cols; with/without spans; `draw()` and `stream()`), printing rows/sec and ms/render. **Measure both a COLD path (a freshly built `Vistab` per render, so `_compute_cols_width` actually runs) and a WARM path (repeated `draw()` on the same object).** This matters because `draw()` memoizes `self._width` and does NOT clear it in its `finally` ([src/vistab.py:1875-1918](file:///home/gfariello/VC/vistab/src/vistab.py)), so a naive reuse loop would measure warm renders only and hide width-computation cost (the exact cost Step 5 targets). Ensure the file is **not collected by `pytest`** (place it outside `tests/`, and/or name it so discovery skips it) and is opt-in, not part of the default suite. Capture a **baseline on `main` before** colspan work. | new `benchmarks/bench_render.py` | Low | Runs locally (see Open Q2 re CI); prints stable cold+warm numbers; `pytest` run time unchanged; baseline documented in the run record. |
| 2 | P1, P7 | Require colspan `_draw_line` to compute each block's width and boundaries **once per row** (before the `for i in range(line_count)` inner loop), e.g. precompute a `col_idx -> (block_width, is_placeholder, colspan)` map for the row and index it in the inner loop. Avoid list-slice allocation on the per-line path (sum in place or reuse the precomputed map). | `src/vistab.py` (colspan impl) | Low | Benchmark: a table with tall wrapped rows + spans is within a small constant factor of the no-span baseline (target: <= ~1.15x render time for equivalent content). |
| 3 | P2 | Require §3.9a junction suppression to precompute the set of suppressed vertical boundaries **once per `draw()`** in a single O(cells) pass (union of spans across header+rows, or per-adjacent-row context built during the single row iteration), then O(1) lookup per boundary while building each rule. Explicitly forbid re-scanning all rows per rule. | `src/vistab.py` (colspan impl) | Low | Benchmark scaling test: render time grows ~linearly with row count (10k rows not disproportionately slower than 10x the 1k time); assert no per-rule full-table scan in code review. |
| 4 | P3, R3 | Reduce per-render allocation in §3.6: prefer mutating the formatted value onto a reused/derived cell or carrying `(value, colspan, is_placeholder, source)` tuples through the render pipeline rather than allocating a second full `VistabCell` per cell per render. If the double-object approach is kept for clarity, cap it to one allocation per cell per render and confirm no per-line allocation. | `src/vistab.py` (colspan impl) | Low | **Allocation must be measured, not asserted:** wrap the cold-path render in `tracemalloc` (peak/allocated-blocks) in the benchmark, OR — if allocation instrumentation is deemed over-scope — drop the allocation-specific claim and validate via cold-path render *time* staying within the Open-Q1 budget. Do not leave an unmeasurable "no super-linear allocation" acceptance criterion. |
| 5 | P4 | Compute each source cell's content width **once** during the §3.5 width pass (store `req` on the cell or a local map), and ensure `str(cell)`/`_len_cell` are not called repeatedly per render. Keep `vislen` on the LRU-cached path (do not pre-strip in a way that produces novel strings that miss the cache). | `src/vistab.py` (colspan impl) | Low | Code review confirms one width computation per source cell per `_compute_cols_width`; benchmark shows width computation cost O(cells), not O(cells x renders-of-same-table beyond the memoization). |
| 6 | P5 | In the colspan plan, make the streaming rule explicit and enforce it: `stream()` keeps sample-derived geometry; spans in post-sample rows are rendered within existing widths (wrap/clip per `on_wrap_conflict`); **no mid-stream `_compute_cols_width`**. Document this as a known limitation in `FUNCTIONAL_SPEC.md` §11 alongside the existing sort caveat. | colspan plan + `FUNCTIONAL_SPEC.md` | Low | Streaming benchmark: per-line time is flat as stream length grows (O(1) per row); a post-sample wide span does not trigger recompute (assert width object identity unchanged). |
| 7 | P6, P1-P5 | Add a performance acceptance line to the colspan plan's Definition of Done: "no-span tables render within a small constant factor of the pre-colspan baseline, and render time is linear in cell count for both `draw()` and `stream()`, proven by `benchmarks/bench_render.py`." | colspan plan §0.3 | Low | The checkbox exists and the benchmark backs it. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are Low Remediation Risk and are proposed for action now. No deferrals. | - |

Explicitly NOT proposed (scope guard): no rewrite of `_compute_cols_width`, `vislen`, or
the wrapping engine for general speed; those are outside the colspan concern and would be
speculative micro-optimization (Complexity axis). This plan only guards against colspan
*introducing* regressions and adds the measurement to prove it.

## Scope check

- **Over-scope:** none proposed. The benchmark (Step 1) is the minimum needed to make the
  other guarantees validatable; it is not gold-plating.
- **Under-scope:** the colspan plan currently has functional tests but **no** performance
  validation and no bound on the F11 rule algorithm; this IPD adds exactly that.

## Required tests / validation

- `benchmarks/bench_render.py`: baseline on `main`, re-run after colspan.
  Report ms/render and rows/sec for: no-span (control), header-span, data-span, and
  span-with-wrapping; for both `draw()` (1k, 10k rows) and `stream()` (streamed 100k rows,
  measuring per-line time flatness). **Report cold and warm separately (R1).** The
  benchmark is opt-in and excluded from `pytest` collection (R5).
- **Performance regression gate:** no-span render time within the Open-Q1 budget of the
  pre-colspan baseline, and render time linear in cell count for `draw()` and `stream()`.
- **Correctness regression gate (shared, not duplicated):** the *byte-identical no-span
  output* test is owned by the colspan plan's Definition of Done (§0.3 item 1) — this IPD
  does not create a second one; it depends on that gate and simply requires it to be green
  before the performance numbers are trusted. (R2: single owner, no divergent golden files.)
- **Complexity assertions (code review):** width computed once per source cell; block
  geometry computed once per row in `_draw_line`; suppressed-boundary set computed once per
  `draw()`; no mid-stream `_compute_cols_width`.

## Spec / documentation sync

- `FUNCTIONAL_SPEC.md` §11: add the streaming/colspan geometry limitation (Step 6).
- If a `benchmarks/` convention is added, note it in `README.md`/`CONTRIBUTING` (if the
  project wants benchmarks documented). N/A to end-user API docs (internal perf only).

## Open questions

1. **Performance budget:** what constant factor is acceptable for no-span tables after the
   object migration (assumption used above: <= ~1.15x)? A human should confirm the target.
2. **Benchmark home / CI:** should `benchmarks/` run in CI as a gate, or be a manual
   pre/post-merge check? (Assumption used throughout this plan: **local pre/post check,
   not a CI gate initially**; Step 1 and the validation section are written to that
   assumption. Confirm before wiring any CI gate.)
3. **Object model vs tuples (Step 4):** is the readability of the double-`VistabCell`
   approach worth its per-render allocation, or should the render pipeline carry lighter
   tuples? Recommend deciding during colspan execution with the benchmark in hand.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, fold Steps 1-7 into the colspan implementation work (they are guardrails on
   that feature), run the benchmark validation, and sync specs/docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`
   per the project lifecycle. Plan files are named `YYYYMMDD-<slug>.md`.
