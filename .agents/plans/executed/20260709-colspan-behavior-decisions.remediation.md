# Remediation Report: Colspan horizontal-rule junction glyphs

- Date: 2026-07-10
- Related plan: `.agents/plans/pending/20260709-colspan-behavior-decisions.md` (executed by Gemini, commit `4554189`)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Status: FIX APPLIED to code + tests (working tree; not yet committed). This report documents what was wrong and what changed.

## Summary

While reviewing the executed colspan work, the maintainer spotted that a horizontal rule
under/over a spanned block rendered a **flat line** where a **directional tee** belongs —
e.g. a plain header sitting above a merged data cell produced:

```
│ N │    A     │    B     │
├───┼─────────────────────┤   <- WRONG: header's │ between A and B dangles into a flat line
```

when it should be:

```
│ N │    A     │    B     │
├───┼──────────┴──────────┤   <- CORRECT: up-tee (┴) terminates the header divider
```

This is a genuine **rendering-correctness bug** in the colspan junction logic (not a
behavior "decision", and not a regression of pre-v1.1.3 functionality since colspan is
net-new). It was introduced with the colspan feature and its committed gold-master fixture
actually *encoded* one instance of the wrong output. Fixed here, with a suite of regression
tests to pin the behavior.

## Root cause

`_build_hline()` ([src/vistab.py:2488](file:///home/gfariello/VC/vistab/src/vistab.py))
decided each interior boundary's glyph with a **binary** rule:

```python
suppressed_boundaries = spanned_above.union(spanned_below)
junction = horiz_char if (boundary_idx in suppressed_boundaries) else mid
```

That collapses four distinct cases into two. A boundary on a horizontal rule can have a
vertical divider **above** and/or **below** independently, and the correct glyph is
directional:

| divider above | divider below | correct glyph | example situation |
|---------------|---------------|---------------|-------------------|
| yes | yes | `┼` cross (`mid`) | normal grid, both rows divide here |
| yes | no  | `┴` up-tee (`_char_new`) | divided row above, merged block below |
| no  | yes | `┬` down-tee (`_char_sew`) | merged block above, divided row below |
| no  | no  | `─` plain (`horiz_char`) | merged on both sides (fully suppressed) |

The old code produced `─` for *both* the "above-only" and "below-only" cases (because
either lands in the union), dropping the `┴`/`┬` and leaving the divider on the adjacent
row visually dangling. The maintainer's report was the "above-only → should be `┴`" case.

A second, related defect surfaced while fixing the first: for a **header-only table**
(no data rows), the bottom border's "row above" was computed as `self._rows[-1]`, which is
empty, so the new directional logic saw *no* divider above and flattened the bottom border.

## The fix (`src/vistab.py`, `_build_hline`)

1. **Directional junction selection** ([src/vistab.py:2544-2560](file:///home/gfariello/VC/vistab/src/vistab.py)).
   Replaced the union/binary logic with per-boundary computation of `divider_above` and
   `divider_below` (each true only when a row exists on that side **and** the boundary is
   not interior to a span in that row), then selects `┼` / `┴` / `┬` / `─` per the table
   above.
   - `mid` already carries the correct arms for TOP (down-tee) and BOTTOM (up-tee)
     locations, so those are unaffected except for genuine suppression.
   - For MIDDLE rules (header separator and between-data-row rules) the one-sided tees are
     `_char_new` (`┴`) and `_char_sew` (`┬`).

2. **Header-only bottom border** ([src/vistab.py:2510-2512](file:///home/gfariello/VC/vistab/src/vistab.py)).
   The row above the bottom border now falls back to the header when there are no data
   rows: `row_above = self._rows[-1] if self._rows else (self._header if self._header else None)`.

No other code paths were touched. The change only affects glyphs at boundaries adjacent to
an actual span or the header-only edge; ordinary tables are unchanged.

## Known limitation (documented, not a defect in this fix)

Double-line-header styles (e.g. `round-header`, whose header separator is `═`) do **not**
provide dedicated header up-tee/down-tee glyphs in the 15-character style vocabulary (only
`_char_hnsew` = `╪`). For those styles a directional tee on the *header separator* falls
back to the single-line `┴`/`┬`, which shows the correct direction but mixes single/double
strokes (ideal would be `╧`/`╤`, which the style does not define). This is a pre-existing
vocabulary limitation, not introduced here; documented for transparency. Non-header rules
and single-line styles are pixel-correct.

## Verification

### Before → after (the maintainer's case)
```
BEFORE                              AFTER
├───┼─────────────────────┤    ->   ├───┼──────────┴──────────┤
```

### Canonical mixed table (spanned header+row0, plain row1)
The committed gold-master `regression_colspan_support.txt` encoded a wrong `─` on the
row0/row1 separator; it now correctly shows a `┬`:
```
├───────┼─────────┬────────┼──────────┤    (row0 merged above, row1 divides below)
```
The fixture was **regenerated** from the corrected output after manual verification (not
blind-regenerated).

### Tests
- Full suite: **86 passed** (was 80; +6 new junction tests). No failures, no warnings.
- New/expanded tests in `tests/test_vistab.py`:
  - `test_colspan_junction_header_sep_up_tee` — plain header over spanned data → `┴` (byte-exact top/sep/bottom).
  - `test_colspan_junction_row_sep_down_tee` — merged row over plain row → `┬`; merged/merged boundary flat.
  - `test_colspan_junction_fully_merged_column` — in-span boundary never gets a junction (byte-exact).
  - `test_colspan_junction_top_and_bottom_borders` — spanned header top border and spanned last-row bottom border suppress the interior junction.
  - `test_colspan_junction_header_only_table` — header-only table keeps full `┬`/`┴` tees (regression for the 2nd defect).
  - `test_colspan_junction_canonical_full_render` — byte-exact render of the full canonical table, pinning every directional junction at once.
  - (existing `test_colspan_junction_suppression` retained.)
- Updated fixture: `tests/fixtures/regression_colspan_support.txt` (corrected `┬`).
- **No-span regression:** verified byte-identical rendering between committed HEAD and the
  fix across 4 styles × {multiline+valign, max_width wrapping, max_rows/max_cols} via a
  temporary worktree diff. The fix does not alter any non-spanned table.

## Files changed

- `src/vistab.py` — `_build_hline`: directional junction logic + header-only bottom-border fallback.
- `tests/test_vistab.py` — 5 new + 1 expanded junction regression tests.
- `tests/fixtures/regression_colspan_support.txt` — regenerated to the corrected output.

## Residual / follow-ups

- **Double-line-header directional tees** (`╧`/`╤`): would require extending the style
  vocabulary (a larger, cross-cutting change to `set_table_lines`/all style definitions).
  Recommend a separate IPD if desired; low user impact.
- This fix is orthogonal to the deferred **B2 auto-alignment** TODO — B2 is about *merging*
  mismatched rows; this fix is about drawing correct glyphs for the rows as they are.
- **Not yet committed.** Suggested commit message:
  `fix(colspan): render directional junctions (┬/┴) on rules adjacent to spans; fix header-only bottom border`
