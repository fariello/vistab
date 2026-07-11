# Implementation Plan - Fix: colspan violates max_width (merged content not wrapped to fit)

Status: REVISED after plan-review (2026-07-11). Ready to execute on approval.

## Plan-review verification (2026-07-11)

Confirmed by reading `_splitit` (`src/vistab.py:3036-3049`): a spanned/source cell IS wrapped
to `w = self._span_block_width(col_idx, colspan)` via `self._cwrap.wrap_list(c, w)`. So the
wrapping machinery for spanned blocks is already correct. The defect is purely that
`_compute_cols_width` expands the columns before `_splitit` runs, so the block never needs to
wrap. The fix approach (stop the over-expansion under `max_width`) is therefore sound: once
the block is left at its budgeted width, `_splitit` wraps the merged content correctly.

Findings folded into this revision: F1/F3 (a naive unconditional skip can shrink a
span's covered columns to near-zero when those columns have little or no standalone content,
producing a block too narrow to wrap legibly), and F2 (add an explicit edge-case test for
that near-zero-column scenario). See "Proposed fix" and "Verification" below.

A spanned (colspan) cell whose merged content is wider than its combined column budget
**expands the columns past `max_width` instead of wrapping**, so the rendered table exceeds
the documented hard width ceiling. Reproduced live while building the showcase demo.

## Prose convention

No em dashes in authored prose (repo/AGENTS.md convention); use periods, commas, colons,
or parentheses.

## Reproduction (verified)

```python
from vistab import Vistab
t = Vistab(style="light", max_width=40)
t.set_header(["A", "B", "C"])
t.add_row(["x", "some long value here", "another long value here too"])
t.add_row(["y", "p", "q"])
t.set_cell_span(0, 1, 2)
print(t.draw())   # renders 56 columns wide, NOT <= 40
```

Observed: `max_width=40` requested, actual visible width **56**. The merged cell content
`some long value here another long value here too` is NOT wrapped; instead the two covered
columns are widened until it fits on one line, blowing the ceiling. A normal (non-spanned)
long cell in the same table would wrap to fit.

## Root cause (verified in `src/vistab.py`)

In `_compute_cols_width()`:
1. The `max_width` shrink (`src/vistab.py:2715-2729`) fits the NON-spanned columns into the
   budget, then sets `self._width = maxi`.
2. The span deficit-distribution (`src/vistab.py:2733-2753`) then runs **after** and
   **unconditionally** does `self._width[j] += base/+1` so the merged content fits on one
   line, with **no `max_width` clamp**. This re-inflates the widths past the ceiling.

So spanned content never wraps under `max_width`; it always widens the table. This is the
"`_max_width` shrink vs. span minimum" interaction the earlier release review flagged as a
risk (deferred there); it is now a confirmed defect.

## Guiding principles / invariants at stake

- `max_width` is documented (README "Limitations & Known Gaps", `docs/API.md set_max_width`,
  `FUNCTIONAL_SPEC`) as a **hard wrapping constraint**: content wraps to fit, and only a
  truly-too-small width raises `ValueError`. Colspan must honor it like every other cell.
- Anti-regression: normal (non-span) `max_width` wrapping must stay byte-identical; spans
  WITHOUT `max_width` must stay byte-identical (the current "expand to fit" behavior is
  correct when there is no ceiling).

## Proposed fix

When `self._max_width` is set and a spanned block's required content width exceeds its
available combined block width, **do NOT expand the columns past the budget; leave the block
within the budget and let `_splitit` wrap the merged content into it** (verified: `_splitit`
already wraps to `_span_block_width(col_idx, colspan)` at `src/vistab.py:3036-3049`).
Concretely:

- In the span distribution loop (`src/vistab.py:2745-2753`): when `self._max_width` is falsy
  (no ceiling), keep the current unconditional deficit expansion (correct, tested behavior).
  When `max_width` IS set, distribute a **bounded** deficit: expand the covered columns only
  up to the width still remaining in the `max_width` budget (never past the ceiling), and
  stop there. Any remaining deficit is left for `_splitit` to wrap.
- **Minimum block width (F1/F3):** do not let the bounded distribution shrink a covered
  column below the existing per-column minimum, and ensure the resulting combined block width
  is at least large enough for `_cwrap.wrap_list` to make progress (the smallest width the
  wrapper accepts for the widest unbreakable token, i.e. the existing over-narrow threshold).
  If that minimum cannot be met within the budget, fall through to the existing
  `on_wrap_conflict` policy / `ValueError` (see edge case below). This prevents the
  near-zero-block failure when a span's covered columns have little or no standalone content.
- Preserve the existing behavior exactly when `max_width` is 0/unset: spans still expand
  columns to fit on one line (that is the correct, tested no-ceiling behavior).
- Edge: if even the minimum block width cannot fit within the budget (extremely small
  `max_width`), fall back to the existing `on_wrap_conflict` policy / `ValueError`, consistent
  with how over-narrow non-span tables behave. Do not invent new error paths.

Rationale for bounded distribution over a plain skip (was Open Question 1): a plain
unconditional skip keeps the covered columns at their `max_width`-shrunk widths, which are
computed from NON-spanned content only (`src/vistab.py:2705` excludes spanned cells from
`maxi`). A column that appears only inside a span can be shrunk to near-zero, making the
merged block impossible to wrap. Bounded distribution (up to the remaining budget, floored at
the minimum block width) gives the span a sane, legible share while still honoring the
ceiling. It is only marginally more code than the skip and is the robust choice.

## Non-goals

- No change to span behavior when `max_width` is unset (columns still expand to fit).
- No change to non-spanned wrapping, alignment, theming, or the color/`--no-color` seam.
- Not redesigning `_compute_cols_width`; a targeted conditional on the deficit expansion.

## Verification

- **Regression pins (must stay byte-identical):**
  - Non-span `max_width` wrapping (a plain long-cell table at `max_width=40`) unchanged vs.
    pre-fix.
  - Spans WITHOUT `max_width` unchanged vs. pre-fix (columns still expand to fit).
- **New tests (`tests/test_vistab.py`):**
  - The reproduction above: with `max_width=40` + a spanned wide cell, the rendered visible
    width (ANSI-stripped) is `<= 40`, and the merged content wraps to multiple lines within
    the block (assert the merged text still fully present across lines, not truncated).
  - Colspan + `max_width` where content already fits: unchanged (no spurious wrapping).
  - **Near-zero-column block (F1/F3):** a span covering columns whose standalone content is
    empty or very narrow, under a tight `max_width`, must still wrap the merged content into
    a legible block (assert visible width `<= max_width` and merged text fully present across
    lines, not collapsed/truncated) rather than crashing or looping in the wrapper.
  - `draw()` does not raise for a reasonable `max_width` with a span; over-narrow still
    errors per existing policy.
- Full `python -m pytest` green (currently 116).
- **Showcase follow-up (separate work):** the showcase expansion is tracked separately and
  runs AFTER this fix, at which point it will exercise colspan + `max_width` end to end. Not
  part of this fix's scope or verification.

## Spec / documentation sync

If any doc implies colspan is exempt from `max_width`, correct it. Add a `CHANGELOG.md`
`[Unreleased]` Fixed entry: "colspan now wraps merged content to honor `max_width` instead
of overflowing the table."

## Open questions

1. **Distribution strategy under max_width:** RESOLVED by plan-review (F3). Use bounded
   deficit distribution (up to the remaining budget, floored at the minimum block width), not
   a plain unconditional skip, because a skip can leave a span's covered columns near-zero
   when they have no standalone content. See "Proposed fix".
2. **Showcase span:** deferred. The showcase is scheduled for a separate, larger expansion
   (tracked as its own follow-up) that will happen AFTER this fix lands, so it can act as a
   real-world stress test of the fix. Do not touch the showcase as part of this fix.

## Approval and execution gate

Proposal only; not executed. On approval: implement the targeted fix, add the regression +
new tests, verify the two byte-identical pins, sync CHANGELOG, and move this IPD to
`.agents/plans/executed/`.
