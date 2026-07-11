# IPD: Colspan usability & grid-integrity hardening

- Date: 2026-07-09
- Concern: ui-ux (API usability) + correctness (grid integrity)
- Scope: The shipped colspan feature in `src/vistab.py` (`ColSpan`, `set_header_span`, `set_cell_span`, `_apply_span_to_list`) and its docs (`docs/API.md`, `README.md`). No changes to the rendering/geometry engine.
- Status: EXECUTED (colspan hardening shipped in 1.2.0). Status corrected 2026-07-11 during release-review 20260711-181922 (stale PENDING line on an executed/-located plan).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Plan-review note (revisions applied):** Reviewed pre-execution; `file:line` claims
> re-verified against `src/vistab.py`. Findings R1-R6 added and addressed. Most important:
> the overlapping-span corruption (U2) can **crash `draw()` with `KeyError`**, not merely
> render a malformed table (verified — see U2 evidence); and the real backward-compat
> constraint is **positional** `ColSpan("x", 2)` (every existing caller uses positional;
> none use `span=`), so Step 1 must guarantee positional binding is preserved. Also
> clarified: whether the coordinate mutators may silently absorb **non-empty** covered
> cells (R3), symmetric `col_idx` validation for `set_header_span` (R4), and the rationale
> for rejecting `colspan < 2` in the mutators (R6).

## Goal

Make the column-spanning API consistent, self-documenting, and safe to misuse. Today the
inline `ColSpan` path is intuitive, but three problems undermine it:

1. **Vocabulary/doc inconsistency:** `ColSpan(value, span=2)` uses `span=`, while every
   other part of the API and the published docs use `colspan`. A user copying
   `docs/API.md` (`ColSpan(value, colspan)`) gets a `TypeError` on first use.
2. **Silent grid corruption (and a crash):** the coordinate mutators
   (`set_cell_span`/`set_header_span`) operate on physical indices with no guard, so
   targeting a placeholder column or creating overlapping spans silently produces a
   malformed table (dropped cells, borders that disagree with data). Worse, some overlap
   sequences leave a placeholder whose `source_cell` is no longer present earlier in the
   row, which makes the render rebuild at [src/vistab.py:1988](file:///home/gfariello/VC/vistab/src/vistab.py)
   (`old_to_new[x.source_cell]`) raise **`KeyError` on `draw()`** — a hard crash on a
   normal path, not just cosmetic corruption.
3. **Inconsistent validation contract:** `ColSpan` requires `span >= 2`, but the mutators
   accept `colspan=1` and even `colspan=0`, and use a different exception type.

Per the user's direction: **accept both** `span=` and `colspan=` on `ColSpan`, fix the
consistency/documentation issues, and fix the ability for spans to break the grid.
Backward-compat note: the load-bearing compatibility case is the **positional** call
`ColSpan("value", 2)` — every existing caller (tests, README, regression fixtures) uses
positional and none use `span=` as a keyword, so Step 1's resolution must keep positional
binding meaning "span".

## Project conventions discovered (Step 0)

- **Stack:** single-module pure-Python library + CLI (`src/vistab.py`). Tests in
  `tests/test_vistab.py` (unittest) and `tests/test_regression.py` (fixture-based).
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`; universal fallback applies —
  intuitive/self-documenting, general-case/configurable, KISS, **no silent failure**,
  honest docs. The grid-corruption bug is a direct "no silent failure" violation.
- **Spec/docs to keep in sync:** `docs/API.md`, `README.md` (§5 Column Spanning),
  `FUNCTIONAL_SPEC.md` (§9 validation/error handling). `CHANGELOG.md` for the fix.
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **Domain invariant at risk (Step 0):** after any span operation the physical row/header
  must stay rectangular (length `self._row_size`) and every source cell
  (`colspan > 1`) must be immediately followed by exactly `colspan - 1` placeholders whose
  `source_cell` is that cell. The current mutators can violate this.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate for acting now.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| U1 | High | Low | Novice / stakeholder | API consistency & honest docs | `ColSpan.__init__(self, value, span=2)` uses `span=`, but `docs/API.md` documents `ColSpan(value, colspan)` and the rest of the API uses `colspan`. `ColSpan("x", colspan=2)` raises `TypeError`. First-use failure for anyone following the docs. | [src/vistab.py:186](file:///home/gfariello/VC/vistab/src/vistab.py); [docs/API.md:59](file:///home/gfariello/VC/vistab/docs/API.md) |
| U2 | Blocker | Low | QA / power user | Grid integrity (no silent failure) | `set_cell_span`/`set_header_span` -> `_apply_span_to_list` do not validate the target. Overlapping spans silently corrupt the grid (dropped column, border row disagreeing with data), and some overlap orders **crash `draw()` with `KeyError`** via the render rebuild (verified: `set_cell_span(0,1,2)` then `set_cell_span(0,0,2)` -> `KeyError` at [src/vistab.py:1988](file:///home/gfariello/VC/vistab/src/vistab.py)). No exception raised at mutation time. | [src/vistab.py:1855-1864](file:///home/gfariello/VC/vistab/src/vistab.py); render rebuild [src/vistab.py:1986-1996](file:///home/gfariello/VC/vistab/src/vistab.py) |
| U3 | Medium | Low | Software engineer | Validation contract consistency | `ColSpan` rejects `span < 2` with `ValueError` ([src/vistab.py:187](file:///home/gfariello/VC/vistab/src/vistab.py)), but `_apply_span_to_list` accepts `colspan` of 1 and 0 without complaint and, for over-range, raises `ValueError` while `set_cell_span` raises `IndexError` for a bad row — three different behaviors for one concept. | [src/vistab.py:1848-1864](file:///home/gfariello/VC/vistab/src/vistab.py) |
| U4 | Low | Low | Novice | Discoverability | The planned `examples/colspan_demo.py` was never added, though README/docs reference the feature. A runnable example is the fastest path to correct first use. | `examples/` has only `basic_usage.py`, `styled_matrix.py` |
| U5 | Low | Low | Software engineer | Docstrings | `set_header_span`/`set_cell_span`/`ColSpan` docstrings do not state that `col_idx`/`row_idx` are **physical** (post-expansion) coordinates, nor the validation rules. Self-documenting gap. | [src/vistab.py:1841-1853](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R1 | Blocker | Low | Testing/QA | Crash on normal path | (Plan-review.) Overlap corruption can crash `draw()` with `KeyError` (render rebuild assumes a placeholder's source precedes it in the row). Step 2 validation prevents it; added a no-crash regression test. | [src/vistab.py:1986-1996](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R2 | High | Low | Software engineer | Backward compat framing | (Plan-review.) Real compat case is **positional** `ColSpan("x", 2)` (all callers positional; none use `span=`). Step 1 must keep positional binding = span. | grep of `ColSpan(` in tests/README/fixtures |
| R3 | Medium | Low | Power user | Silent data loss | (Plan-review.) A coordinate mutator spanning over already-populated columns silently discards their values. Default now: raise (Open Q3). | Step 2 rule; [src/vistab.py:1855-1864](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R4 | Medium | Low | Software engineer | Asymmetric index validation | (Plan-review.) `set_header_span` lacks the `col_idx` bounds guard `set_cell_span` has for `row_idx`. Step 3 adds symmetric `IndexError`. | [src/vistab.py:1841-1853](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R5 | Low | Low | QA | Partial mutation | (Plan-review.) `_apply_span_to_list` mutates in a loop; validation must run first so rejection leaves the grid unchanged. Step 2 now requires validate-before-mutate + a grid-unchanged test. | [src/vistab.py:1861-1864](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R6 | Low | Low | Power user | Surprising `colspan=1` reject | (Plan-review.) Rejecting `colspan=1` (vs treating it as "no span") may surprise callers passing a computed value. Documented as a deliberate choice; revisit via Open Q1. | Step 2/Open Q1 |

## Proposed changes (ordered, validatable)

Fix-by-default; all are Low Remediation Risk (additive/validation, no engine changes).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | U1, R2 | **Accept both `span` and `colspan` on `ColSpan`.** Change the signature to `def __init__(self, value, colspan=None, span=None)`. **The second positional parameter MUST remain the span** so `ColSpan("x", 2)` (the form every existing caller uses) still yields span 2 — this is the load-bearing compat guarantee, hence `colspan` is the second positional. Resolve the effective value: if both `colspan` and `span` are given and unequal -> `ValueError`; if neither -> default `2`; otherwise use whichever was provided. Store on `self.span` (keep the attribute name so `_expand_spans_in_row` at [src/vistab.py:897](file:///home/gfariello/VC/vistab/src/vistab.py) is unchanged) and expose `self.colspan` as an alias for symmetry with `VistabCell.colspan`. Keep the `>= 2` validation on the resolved value. | `src/vistab.py` | Low | New unit test: `ColSpan("x", 2)` (positional), `ColSpan("x", colspan=2)`, and `ColSpan("x", span=2)` all produce span 2 **and** `.colspan == 2`; `ColSpan("x", span=2, colspan=3)` raises `ValueError`; `ColSpan("x", colspan=1)` raises `ValueError`. Existing tests/fixtures (all positional) pass unchanged. |
| 2 | U2, U3, R1, R3, R5 | **Add grid-integrity validation to `_apply_span_to_list`** (the single choke point for both mutators). **Validate fully BEFORE any `row_list[...] =` assignment** so a rejected call leaves the grid byte-for-byte unchanged (no partial mutation; note the current code mutates in a loop at [src/vistab.py:1861-1864](file:///home/gfariello/VC/vistab/src/vistab.py)). Reject with a clear `ValueError`: (a) resolved span `< 2`; (b) target `col_idx` is a `VistabPlaceholderCell` (inside an existing span) — message names the owning source column; (c) any column in `[col_idx, col_idx+colspan)` other than the target is a source with `colspan > 1` OR a placeholder of a *different* source (would overlap/truncate an existing span). **(R3) Decide the covered-non-empty-cell policy:** if any covered slot `(col_idx, col_idx+colspan)` currently holds a non-empty value that the span would discard, the default is to **raise `ValueError`** ("span would overwrite non-empty cell at col N; clear it first") rather than silently drop data — matching "no silent failure". (Confirm via Open Q3.) **(R1) Preserve the render-rebuild ordering invariant** at [src/vistab.py:1986-1996](file:///home/gfariello/VC/vistab/src/vistab.py): a placeholder's `source_cell` must always appear earlier in the same row; the validated span construction guarantees this. Keep the existing out-of-range check. | `src/vistab.py` | Low | New unit tests: overlapping `set_cell_span(0,0,2)`+`set_cell_span(0,1,2)` (both orders) raises `ValueError`; the grid contents are identical to before the rejected call; `set_cell_span` onto a placeholder raises; `colspan=1`/`0` raises; covering a non-empty cell raises (per Open Q3); adjacency invariant holds after a legal span; **`draw()` never raises `KeyError` for any sequence of `set_*_span` calls** (regression for the crash). |
| 3 | U3, R4 | **Unify the exception contract, symmetrically.** Invalid *arguments* (bad `colspan`, overlap, placeholder target, covered-non-empty) -> `ValueError`; out-of-range *index* (`row_idx`/`col_idx` beyond the grid) -> `IndexError`. **(R4)** `set_cell_span` already guards `row_idx` ([src/vistab.py:1850](file:///home/gfariello/VC/vistab/src/vistab.py)); add the symmetric guard so a negative or too-large `col_idx` raises `IndexError` in **both** `set_cell_span` and `set_header_span` (today `set_header_span` only checks that a header exists, and the current over-range check raises `ValueError` — reclassify pure index-out-of-range to `IndexError`, keeping `colspan`-too-large-for-remaining-columns as a `ValueError` argument error). Note the mapping in each docstring. | `src/vistab.py` | Low | Exception-type matrix test covers `set_cell_span` and `set_header_span` for: bad row_idx, bad col_idx (both negative and too-large), bad colspan, overlap, placeholder target — asserting `IndexError` vs `ValueError` exactly, matching docstrings and `docs/API.md`. |
| 4 | U1, U3, U5 | **Fix and expand documentation.** Update `docs/API.md`: `ColSpan(value, colspan=2)` (note `span=` accepted as an alias), and document that `set_*_span` use **physical** column indices and their validation/exception rules. Update `README.md` §5 if wording implies logical indices. Add the validation behavior to `FUNCTIONAL_SPEC.md` §9. Add a `CHANGELOG.md` entry. | `docs/API.md`, `README.md`, `FUNCTIONAL_SPEC.md`, `CHANGELOG.md` | Low | Docs match the code (a doctest-style copy of each documented call runs without error); reviewer confirms no doc claims a call the code rejects. |
| 5 | U4, U5 | **Add `examples/colspan_demo.py`** demonstrating both the inline `ColSpan` and the coordinate mutators, incl. a header spanning subcolumns and a wide wrapped data span; and flesh out the `ColSpan`/`set_*_span` docstrings with the physical-index note and a short example. | `examples/colspan_demo.py`, `src/vistab.py` (docstrings) | Low | `python examples/colspan_demo.py` runs and prints a well-formed table; docstrings render cleanly. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are Low Remediation Risk and proposed for action now. | - |

**Explicitly NOT proposed (scope guard, KISS):**
- Do **not** switch the mutators to *logical* (user-facing) coordinates. That is a larger
  behavior change with its own ambiguity (how to address a placeholder logically) and
  would risk the rendering engine's physical-coordinate invariants (Complexity +
  Functionality). Validating physical coordinates and documenting them clearly (Steps 2-4)
  delivers the safety the user asked for without that risk. If logical addressing is
  wanted later, it is a separate IPD.
- No rework of the geometry/rendering engine (`_build_hline`, `_span_block_width`,
  `_draw_line`); these are correct and out of scope.

## Scope check

- **Over-scope:** none. Steps map 1:1 to the three user-stated goals (accept both;
  consistency + docs; fix grid-breaking).
- **Under-scope:** the shipped feature lacks input validation and a runnable example;
  Steps 2 and 5 add exactly those.

## Required tests / validation

- **New unit tests (`tests/test_vistab.py`):**
  - `ColSpan` accepts positional `("x", 2)`, `colspan=`, and `span=` (all yield span 2 and
    `.colspan == 2`); rejects conflicting values and `< 2` (Step 1, R2).
  - `_apply_span_to_list` rejects overlap (both orderings), placeholder target,
    `colspan < 2`, and covering-non-empty (per Open Q3); grid contents **identical** after a
    rejected call (no partial mutation, R5); adjacency invariant holds after a legal span.
  - **No-crash regression (R1):** for the previously-crashing sequences
    (`set_cell_span(0,1,2)` then `set_cell_span(0,0,2)`, and vice-versa) the mutator now
    raises `ValueError` and, for any accepted sequence, `draw()` never raises `KeyError`.
  - Exception-type matrix (`ValueError` vs `IndexError`) for both `set_cell_span` and
    `set_header_span`, including bad `col_idx` (negative and too-large) per Step 3/R4.
- **Regression:** the existing colspan tests (`test_colspan_*`, `test_set_span_api`,
  `test_regression_colspan_support`) must still pass unchanged — behavior for *valid* spans
  must not change. Run the full suite (`python -m pytest`).
- **Manual:** `python examples/colspan_demo.py` produces a correct table.

## Spec / documentation sync

- `docs/API.md`: correct `ColSpan` signature + physical-index/validation notes (Step 4).
- `README.md` §5: align wording; keep the inline example as the lead.
- `FUNCTIONAL_SPEC.md` §9: add colspan validation/error behavior.
- `CHANGELOG.md`: entry for the `colspan=` alias and the new validation.

## Open questions (Resolved)

1. **`colspan=1` semantics (R6):**
   - **Decision**: Treat `colspan=1` as a **no-op** (returns immediately without exception, does not mutate, and does not create placeholders). This ensures computed spans that resolve to 1 do not crash the caller. Spans `< 1` are still rejected.
2. **Alias direction:**
   - **Decision**: Standardize and rename internal attributes to `colspan` globally (e.g. on `ColSpan` and `VistabCell` objects) rather than just keeping a property alias.
3. **Covered non-empty cells (R3):**
   - **Decision**: **Raise `ValueError`** if a coordinate mutator would overwrite a non-empty cell (e.g., cell value is not `None`, `""`, or placeholder). This enforces the "no silent failure" guideline and prevents accidental data loss. Caller must explicitly clear columns to be covered.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute Steps 1-5 in order, run the validation, and sync docs/spec.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`
   per the project lifecycle. Plan files are named `YYYYMMDD-<slug>.md`.
