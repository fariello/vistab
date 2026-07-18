# Implementation Plan Document (IPD): Column Spanning (Colspan) Support

* **Target Milestone**: Column Spanning (Case 1: Headers & Case 2: Data Cells)
* **Status**: Pending Review
* **Plan Path**: `.agents/plans/pending/20260709-colspan-support.md`
* **Subsequent Work**: A future IPD will address Row Spanning (Case 3: Rowspans & Case 4: Row/Colspans). The architecture defined here is explicitly designed to lay the foundation for that work.

> **Plan-review note (revisions applied):** This plan was reviewed pre-execution
> against the actual source in [src/vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py).
> The original draft under-specified several places where the *existing* code assumes
> cells are plain strings, which would break as soon as cells become `VistabCell`
> objects. Two review passes were applied. Pass 1 added the string-transparency rule in
> 3.1, Sections 3.1a/3.2/3.4b/3.5, and Section 5 (cross-cutting constraints). Pass 2
> (hardening for a fast implementer) added: **§0 Implementer Contract** (Definition of
> Done, mandatory order, scope fence); **§3.0** a single centralized span-geometry helper
> (`_sep_width`/`_span_block_width`) that §3.5/§3.8/§3.9/§3.9a must all use to prevent
> drift; **§3.9a / F11** horizontal-rule junction suppression (the original plan omitted
> `_build_hline`, which would ship broken box-drawing under spans); corrected the §3.5
> width-distribution from a buggy `deficit/(k+1)` float split to an exact `divmod` over
> `k` columns; and rewrote §4 tests to assert exact output/invariants instead of "does
> not crash." Guiding principles: no project
> `GUIDING_PRINCIPLES.md`/`PRINCIPLES.md` exists, so the universal fallback principles
> (intuitive/self-documenting, general-case/configurable, KISS, honest docs) were used,
> plus the `FUNCTIONAL_SPEC.md` invariant that additions "must preserve backward
> compatibility."

---

## 0. Implementer Contract (READ THIS FIRST — do not skip)

This section exists because the rest of the plan is detailed and it is tempting to
implement the "happy path" pseudocode in §3 and skip the cross-cutting constraints in
§5. **Do not do that.** The constraints are where the real bugs live. Work in the order
below, and treat the Definition of Done as the acceptance gate.

### 0.1 The ONE rule that prevents 80% of the bugs here
Span geometry (how wide a spanned block is, and where its boundaries fall) is needed
identically in three separate methods (`_compute_cols_width`, `_splitit`, `_draw_line`)
**and** in the horizontal-rule builder (`_build_hline`). If you hand-code that math four
times it *will* drift and the borders/wrapping/widths will disagree.

**Implement exactly ONE helper and call it everywhere** (see §3.0):
```python
def _span_block_width(self, start_col: int, colspan: int) -> int:
    """Total interior width of a spanned block, in characters, including the
    inter-column gaps that are absorbed into the merged cell.
    interior = sum(self._width[start_col : start_col+colspan])
             + (colspan - 1) * self._sep_width()
    """
```
where `_sep_width()` is the width of one inter-column gap =
`2 * self._pad + (1 if self.has_vlines() else 0)`. Never inline this arithmetic anywhere
else. If a reviewer finds the separator math (`2*pad + ...`) copy-pasted into a second
method, that is a defect to fix, not a style nit.

### 0.2 Mandatory implementation order (each step must leave tests green)
1. **Data model** (§3.1): add `ColSpan`, `VistabCell`, `VistabPlaceholderCell`, and the
   mandatory `__str__`. Add `_sep_width()` and `_span_block_width()` (§3.0). *Run the
   existing suite — it must stay green because nothing uses the new classes yet.*
2. **Ingestion** (§3.2, §3.4): `_expand_spans_in_row`, fix `set_header`'s `obj2unicode`
   line, expand-before-size-check. *Existing suite still green* (rows of plain values
   now become `VistabCell(...)` with `colspan=1`; string-transparency keeps everything
   working). This is the single most important regression checkpoint: **if any existing
   test breaks here, stop and fix it before adding span behavior.**
3. **Draw/stream metadata preservation** (§3.6) + `_str`/`_len_cell` object handling
   (§3.1a).
4. **Width** (§3.5) using `_span_block_width`.
5. **Wrapping** (§3.8) and **drawing** (§3.9) using `_span_block_width`, honoring §5.1.
6. **Horizontal rules** (§3.9a / F11) — suppress junctions inside a span.
7. **Mutators** (§3.3), **`_max_cols` clipping** (§3.7), **sorting** (§3.4b).
8. **Cross-cutting** (§5): ANSI sanitization (§5.2), zebra parity (§5.3), `_max_width`
   interaction (§5.4).
9. **Tests** (§4), **spec/docs/changelog sync** (§5.5).

### 0.3 Non-negotiable invariants (Definition of Done)
The milestone is NOT done until every box is true. Add an assertion or test for each.
- [ ] **Backward compatibility:** the full existing test suite passes unchanged, and a
      table built with **no** spans renders byte-for-byte identically to `main`. Add a
      golden-output regression test proving this (see §4.1 item 6).
- [ ] **Rectangularity:** after ingestion and after `_max_cols` clipping, every row and
      the header have length `self._row_size`; `sum` of physical widths still maps 1:1 to
      `self._width`, `self._align`, `self._valign`, `self._header_align`.
- [ ] **Adjacency:** a source cell (`colspan > 1`) is always immediately followed by
      exactly `colspan - 1` placeholders whose `source_cell` is that cell — before AND
      after `sort_by`.
- [ ] **Geometry agreement:** for every spanned block, the width used for wrapping
      (§3.8), for drawing the cell (§3.9), and the run of horizontal-rule characters
      under/over it (§3.9a) are all `_span_block_width(start, colspan)`. No off-by-one at
      the block boundary.
- [ ] **No junction artifacts:** horizontal rules show NO vertical-junction character
      (`┬ ┼ ┴` etc.) piercing the interior of a spanned block (F11 / §3.9a).
- [ ] **ANSI safety preserved:** spanned content passes through the exact same
      `_sanitize_destructive_ansi` / context-reassertion path as a normal cell (§5.2).
- [ ] **No copy-pasted geometry:** separator/width math exists in `_sep_width` /
      `_span_block_width` only (§0.1).
- [ ] **Docs synced:** `FUNCTIONAL_SPEC.md`, `docs/API.md`, `CHANGELOG.md` updated (§5.5).

### 0.4 Do NOT touch (scope fence)
Changing these to "make spans work" is a sign of a wrong approach — fix the span code
instead: the public signatures of `draw`/`stream`/`add_row`/`set_header` (additive only),
the ANSI sanitization routines, the `_max_width` shrink *algorithm* (you may sequence
around it per §5.4, not rewrite it), and any pre-existing test's expected output. The 6
pre-existing failures in `tests/test_regression.py` (CLI/theme/edge) are unrelated to
this work — do not "fix" them here and do not let them mask new regressions.

---

## 1. Goal & Context

`Vistab` currently renders text tables by formatting cell values as strings and laying them out in a rigid 2D grid structure. Each column has a single calculated width. 

This change introduces **Column Spanning (Colspan)** support for both header cells (Case 1) and data cells (Case 2). Since Case 2 is a superset of Case 1, we implement a unified column-spanning layout engine.

### Architectural Constraint (Preparing for Cases 3 & 4)
A subsequent IPD will address row spanning (vertical merge). To avoid making row spans more challenging, we migrate the internal cell grid representation from list-of-lists of raw strings to a **Grid of Cell Objects with Sentinel Placeholders**. This keeps the grid physically rectangular ($M \times N$), which:
1. Avoids breaking existing matrix check constraints (`_check_row_size`).
2. Keeps column styling maps and horizontal border calculations aligned with physical coordinates.
3. Provides a clean hook for vertical rowspan placeholders later (e.g. `RowSpannedPlaceholderCell` to route multi-line text vertically and suppress horizontal borders).

---

## 2. API Design

### 2.1 Inline Programmatic API (`ColSpan` Wrapper)
Users can specify column spans inline when populating headers or rows.
```python
from vistab import Vistab, ColSpan

table = Vistab()
table.set_header(["Name", ColSpan("Contact Details", span=2), "Age"])
table.add_row(["Alice", ColSpan("alice@example.com / 555-0199", span=2), 25])
```
*Note: To keep the list length aligned with column dimensions, the user must provide either matching sentinel slots (e.g., `None` or `""` for the spanned columns) OR the ingestion pipeline must automatically expand the array internally.*
To avoid breaking `_check_row_size()` validation, the `Vistab` data ingestion logic will automatically unpack `ColSpan` wrapper objects and inject internal placeholders into the row.

### 2.2 Coordinate-Based Styling API
Allows users to declare column spans after loading data (ideal for CSV imports or CLI workflows):
```python
# API Methods
table.set_header_span(col_idx=1, colspan=2)
table.set_cell_span(row_idx=0, col_idx=1, colspan=2)
```

---

## 3. Proposed Changes

All modifications are confined to [src/vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py).

### 3.0 Centralized Span Geometry (single source of truth — build this first)
Add two small helpers to `Vistab` and route **all** span-width math through them. This is
the architectural keystone of the whole feature (see §0.1); implementing it first makes
§3.5, §3.8, §3.9, and §3.9a trivial and consistent.

```python
def _sep_width(self) -> int:
    """Width, in characters, of one inter-column gap that a span absorbs.
    Matches how draw()/_build_hline compute the gap between two columns:
    left pad + optional vertical rule + right pad.
    """
    return 2 * self._pad + (1 if self.has_vlines() else 0)

def _span_block_width(self, start_col: int, colspan: int) -> int:
    """Total interior render width of a spanned block covering
    [start_col, start_col + colspan) physical columns."""
    interior = sum(self._width[start_col:start_col + colspan])
    interior += (colspan - 1) * self._sep_width()
    return interior
```

Rationale / correctness notes for the implementer:
- The gap width `2*pad + (1 if has_vlines)` is exactly the `cell_sep`/`v_delim`
  arithmetic already used in `_build_hline` ([src/vistab.py:2238](file:///home/gfariello/VC/vistab/src/vistab.py))
  and `_draw_line` ([src/vistab.py:2513](file:///home/gfariello/VC/vistab/src/vistab.py)).
  Deriving it once here guarantees widths, wrapping, drawing, and rules agree.
- A `colspan == 1` call returns just `self._width[start_col]`, so ordinary cells can use
  the same code path with no special-casing (KISS; fewer branches for a sloppy caller to
  get wrong).
- `_span_block_width` requires `self._width` to exist, so it may only be called during/
  after `_compute_cols_width`. Note that in your call sites.

### 3.1 Structural Data Models
We add internal classes at the module level:

```python
class ColSpan:
    """Public wrapper to define column spanning inline during data initialization."""
    def __init__(self, value: Any, span: int = 2):
        if not isinstance(span, int) or span < 2:
            raise ValueError("Span must be an integer >= 2")
        self.value = value
        self.span = span

class VistabCell:
    """Internal cell representation holding span metadata."""
    def __init__(self, value: Any, colspan: int = 1, rowspan: int = 1):
        self.value = value
        self.colspan = colspan
        self.rowspan = rowspan
        self.is_placeholder = False
        self.source_cell = None

class VistabPlaceholderCell(VistabCell):
    """Sentinel placeholder occupying coordinates covered by a spanned cell."""
    def __init__(self, source_cell: VistabCell):
        super().__init__(value="")
        self.is_placeholder = True
        self.source_cell = source_cell
        self.colspan = source_cell.colspan
        self.rowspan = source_cell.rowspan
```

> **MANDATORY: `VistabCell` must be string-transparent.** The existing engine assumes
> cells are plain strings in many hot paths that this plan does **not** rewrite, e.g.
> `str(row[col_idx])` in `_apply_sorting` ([src/vistab.py:1142](file:///home/gfariello/VC/vistab/src/vistab.py)),
> `str(row[c])` in `_infer_auto_dtypes` ([src/vistab.py:2366](file:///home/gfariello/VC/vistab/src/vistab.py))
> and `_check_align` ([src/vistab.py:2425](file:///home/gfariello/VC/vistab/src/vistab.py)),
> and `cell.split('\n')` in `_len_cell` ([src/vistab.py:2256](file:///home/gfariello/VC/vistab/src/vistab.py)).
> To avoid rewriting all of those (KISS), `VistabCell` MUST define `__str__` returning
> `str(self.value)`. This is a load-bearing requirement, not optional:
> ```python
>     def __str__(self):
>         return "" if self.value is None else str(self.value)
> ```
> A placeholder's `__str__` therefore yields `""`, so sorting/dtype-inference/alignment
> keys derived from placeholders are empty and neutral. Add `__str__` to `VistabCell`.

### 3.1a Single Source of Truth: cells become objects at ingestion time
The original draft was ambiguous: Section 3.2 converts to objects at ingestion, while
Section 3.6 re-wraps at draw time. Resolve this explicitly:

- **Canonical internal representation:** after `set_header`/`add_row`, `self._header`
  and every row in `self._rows` hold a rectangular ($M\times N$) list of `VistabCell` /
  `VistabPlaceholderCell` objects. This is the ONE source of truth. All new code
  (`_apply_span_to_list`, width, wrapping, drawing) operates on objects.
- **Draw-time (`_str`) does NOT re-wrap into new objects blindly (revises 3.6):** it
  formats `cell.value` in place and returns a *new* `VistabCell` copying `colspan`,
  `rowspan`, `is_placeholder`, and `source_cell`, so metadata is never lost. Placeholder
  cells are passed through unchanged (their formatted value stays `""`).
- **`_str` and `_len_cell` inputs:** `_str(i, x)` and `_len_cell(cell)` are called with
  objects. `_str` must read `x.value` when `x` is a `VistabCell`; `_len_cell` must read
  `str(cell)` (safe via the mandatory `__str__`) before `.split('\n')`. Update both
  signatures' bodies accordingly rather than relying on strings.

### 3.2 Data Ingestion & Placeholder Expansion
In `set_header` and `add_row`, we convert lists of raw items into lists of `VistabCell` and `VistabPlaceholderCell` objects.

> **BLOCKER fix — `set_header` currently stringifies everything.** Today
> `set_header` does `self._header = list(map(obj2unicode, processed_array))`
> ([src/vistab.py:1772](file:///home/gfariello/VC/vistab/src/vistab.py)), which would
> convert any `ColSpan`/`VistabCell` into its `repr`/`__str__` string and permanently
> destroy header span metadata — header spans (Case 1) could never work. This plan MUST
> replace that line so the header holds expanded `VistabCell` objects:
> `self._header = self._expand_spans_in_row(processed_array)`. Header cells are then
> object-typed exactly like data rows (see 3.1a), keeping the two paths symmetric. Any
> downstream code that assumed `self._header` is a list of strings (e.g. `_len_cell`
> over `self._header` in `_compute_cols_width` at
> [src/vistab.py:2300](file:///home/gfariello/VC/vistab/src/vistab.py)) is covered by
> the string-transparency rule in 3.1 and the width updates in 3.5.

```python
def _expand_spans_in_row(self, row: List[Any]) -> List[VistabCell]:
    expanded = []
    i = 0
    while i < len(row):
        item = row[i]
        if isinstance(item, ColSpan):
            cell = VistabCell(item.value, colspan=item.span)
            expanded.append(cell)
            for _ in range(item.span - 1):
                expanded.append(VistabPlaceholderCell(cell))
        elif isinstance(item, VistabCell):
            expanded.append(item)
            if item.colspan > 1:
                for _ in range(item.colspan - 1):
                    expanded.append(VistabPlaceholderCell(item))
        else:
            expanded.append(VistabCell(item))
        i += 1
    return expanded
```

This method will run *after* raw data parsing, but *before* strict length validation is checked (or `_check_row_size` will be updated to validate the *expanded* logical row size).

### 3.3 Dynamic Span Mutation APIs
Add standard coordinate mutators to `Vistab`:
```python
def set_header_span(self, col_idx: int, colspan: int) -> 'Vistab':
    """Set the column span of a specific header cell."""
    if not self._header:
        raise ValueError("Header must be set before applying spans.")
    self._apply_span_to_list(self._header, col_idx, colspan)
    return self

def set_cell_span(self, row_idx: int, col_idx: int, colspan: int) -> 'Vistab':
    """Set the column span of a specific data cell."""
    if row_idx >= len(self._rows):
        raise IndexError("Row index out of range.")
    self._apply_span_to_list(self._rows[row_idx], col_idx, colspan)
    return self

def _apply_span_to_list(self, row_list: List[VistabCell], col_idx: int, colspan: int):
    if col_idx + colspan > len(row_list):
        raise ValueError(f"Span of {colspan} exceeds column count limit of {len(row_list)}.")
    
    # Create the source cell
    source_val = row_list[col_idx].value if isinstance(row_list[col_idx], VistabCell) else row_list[col_idx]
    source_cell = VistabCell(source_val, colspan=colspan)
    row_list[col_idx] = source_cell
    
    # Overwrite subsequent cells with placeholders
    for offset in range(1, colspan):
        row_list[col_idx + offset] = VistabPlaceholderCell(source_cell)
```

### 3.4 Ingestion & Size Check Updates (`_check_row_size`)
- In `add_row()` and `set_header()`, we will expand `ColSpan` inline items into `VistabCell` and placeholder sentinels **before** invoking `_check_row_size()`.
- We will modify `_check_row_size()` to validate the *expanded* row length. This ensures that a row like `["Val 1", ColSpan("Spanned", 2)]` is recognized as having a logical length of 3 (1 normal + 2 spanned), matching the expected `self._row_size = 3` rather than failing as a "short row" of length 2.

### 3.4b Sorting Interaction (`_apply_sorting`) — keep spans atomic
`_apply_sorting` sorts `self._rows` in place per-row using `str(row[col_idx])`
([src/vistab.py:1148](file:///home/gfariello/VC/vistab/src/vistab.py)). Two problems must
be handled or Test 4.1-item-4 (sorting) will silently corrupt output:
1. **Sort key on objects:** `str(row[col_idx])` is safe only because of the mandatory
   `VistabCell.__str__` (3.1). Confirm `parse_val` still reads a sensible key; a sorted
   column that is itself a placeholder yields `""` — acceptable, but document it.
2. **Atomicity of a spanned block within a row:** sorting reorders whole rows, not cells
   within a row, so a source cell and its trailing placeholders stay adjacent (they never
   move relative to each other). This is inherently safe for **column** spans and is the
   reason column spanning is tackled before row spanning. Add a regression assertion that
   after `sort_by`, each source cell is still immediately followed by exactly
   `colspan - 1` placeholders referencing it (see Test 4.1-item-4). Row spans (future
   IPD) will break this and must re-block rows before sorting; note that constraint here
   so the future work inherits it.

### 3.5 Column Width Calculation (`_compute_cols_width`)
The layout sizing code in `_compute_cols_width()` must distribute spanned cell widths:
1. Compute standard maximum cell lengths for all columns using only non-spanned cells (`cell.colspan == 1` and not `cell.is_placeholder`). All cells are `VistabCell` objects by 3.1a; use `self._len_cell(str(cell))` (string-transparent per 3.1). Placeholder and source (`colspan > 1`) cells contribute **0** to their physical column's base width in this pass, so a wide spanned value does not inflate a single column.
2. Iterate through all spanned cells (`cell.colspan > 1`, starting at physical column `c`, `k = colspan`).
3. Calculate the required content width of the spanned cell: `req = self._len_cell(str(cell))` (string-transparent per §3.1).
4. Compare `req` with the current combined width **via the shared helper** (do NOT re-derive the separator arithmetic here — see §0.1):
   `curr = self._span_block_width(c, k)`.
5. If `req > curr`, distribute the deficit `deficit = req - curr` as evenly as possible
   among the `k` covered columns:
   `base, extra = divmod(deficit, k)`; add `base` to every `self._width[j]` for
   `j in range(c, c+k)`, and `+1` to the first `extra` of them. Using integer
   `divmod` (not float division) guarantees the columns sum back to exactly `req` with no
   rounding drift — a source of off-by-one border misalignment if done with `/`.

> Note: run this distribution pass **after** any `_max_width` shrink; see §5.4.

### 3.6 String Formatting Refactoring (`draw` and `stream`)
Currently, `draw()` and `stream()` replace `self._rows` with raw lists of formatted strings (`cells = [self._str(i, x) for x in row]`), which drops the cell objects and their colspan/placeholder metadata.
- We will modify the formatting block in `draw()` and `stream()` to wrap the formatted output back into `VistabCell` objects:
  ```python
  formatted_val = self._str(i, x.value if isinstance(x, VistabCell) else x)
  if isinstance(x, VistabCell):
      new_cell = VistabCell(formatted_val, colspan=x.colspan, rowspan=x.rowspan)
      new_cell.is_placeholder = x.is_placeholder
      new_cell.source_cell = x.source_cell
      cells.append(new_cell)
  else:
      cells.append(VistabCell(formatted_val))
  ```
  This preserves cell structures during subsequent width-checking, wrapping, and rendering phases.

### 3.7 Clipping Constraints (`_max_cols`)
When `self._max_cols` is configured:
- After slicing the rows to `self._rows = [row[:self._max_cols] for row in self._rows]`, we must adjust the `colspan` property on any cell that starts before the boundary but spans past it, capping it to the new sliced length:
  ```python
  for row in self._rows:
      for i, cell in enumerate(row):
          if isinstance(cell, VistabCell) and not cell.is_placeholder:
              if i + cell.colspan > len(row):
                  cell.colspan = len(row) - i
  ```
  This prevents index out-of-range or sizing exceptions on truncated spanned blocks.

### 3.8 Text Wrapping (`_splitit`)
Update `_splitit` to wrap text to the combined width of the span:
- When iterating through columns:
  - If a cell is a `VistabPlaceholderCell`, append an empty list `[]` to `line_wrapped` (it will be padded to match the row's vertical lines).
  - If a cell is a normal cell or the source cell of a span:
    - Compute the wrap width with the shared helper: `w = self._span_block_width(col_idx, cell.colspan)` (this returns the single-column width when `colspan == 1`, so there is no special case — see §0.1).
    - Wrap the cell's text using `self._cwrap.wrap_list(text, w)`.
    - **Line-count parity (§5.1):** after wrapping every cell, pad each cell's wrapped
      line-list (including the `[]` placeholders) to the row's maximum line count so the
      outer `for i in range(...)` loop in `_draw_line` never indexes past the end.

### 3.9 Row Line Drawing (`_draw_line`)
Update `_draw_line`'s column drawing loop to skip placeholders and span columns:
- Loop through columns using `col_idx` from `0` to `num_cols`:
  - Fetch `cell_obj = original_line[col_idx]`.
  - If `isinstance(cell_obj, VistabPlaceholderCell)`:
    - **Skip** (increment `col_idx += 1` and continue).
  - Otherwise, this is a drawable cell:
    - Retrieve `colspan = cell_obj.colspan`.
    - Compute the combined width with the shared helper: `width = self._span_block_width(col_idx, colspan)`.
    - Fetch alignment from the **source** column: `align = self._align[col_idx]` (or `self._header_align[col_idx]` for headers) — see §5.1; do not `zip` over the physical-length lists once you advance by `colspan`.
    - Render the cell line aligned inside this combined width (reuse the existing fill/align/clip block verbatim so `on_wrap_conflict` behavior is preserved).
    - Apply the SAME `_sanitize_destructive_ansi` / `_reassert_ansi_context` steps as the single-cell path (§5.2) — do not skip them for spans.
    - Output the right padding and vertical separator ONLY at the boundary of the spanned block (i.e., after physical column `col_idx + colspan - 1`).
    - Advance `col_idx += colspan`.

### 3.9a Horizontal-Rule Junction Suppression (`_build_hline`) — F11 (BLOCKER)
**The original plan omitted `_build_hline` entirely, but it is where spanned box-drawing
visibly breaks.** Today `_build_hline`
([src/vistab.py:2219](file:///home/gfariello/VC/vistab/src/vistab.py)) joins every
physical column with a junction character (`mid`, e.g. `┬`/`┼`/`┴`) and knows nothing
about spans. A header/row with a colspan therefore gets a `┬`/`┼`/`┴` poking up/down into
the middle of the merged block, so the boxes look broken — the very thing §4.2 claims to
verify.

Required behavior:
- A horizontal rule sits *between* two rows (or above/below the header). At each interior
  physical column boundary `b` (between column `b-1` and `b`), draw the junction
  character **only if that boundary is a real cell edge in BOTH the row above and the row
  below** the rule. If a span in the row above OR below crosses boundary `b` (i.e. `b` is
  interior to some spanned block), replace the junction with the plain horizontal
  character (`horiz_char`) so the rule reads as continuous under the merged cell.
- Concretely: `_build_hline` must become **row-context aware**. Pass it the cell lists of
  the adjacent row(s) (it is called from `draw`/`stream` where those are in scope) and
  build a set of "suppressed boundaries" = every interior boundary covered by a span in
  either neighbor. TOP/BOTTOM rules consider only the single adjacent row (header row for
  TOP, last row for BOTTOM); the header-separator considers header + first data row;
  MIDDLE rules consider the two data rows they separate.
- The run of characters spanning a merged block must be exactly `_span_block_width(start,
  colspan)` wide (Definition-of-Done "geometry agreement"), so the corner/edge characters
  still line up with the vertical rules that DO exist at the block's outer boundaries.
- Keep it simple: if computing per-rule neighbor context is awkward for the streaming
  path, it is acceptable to compute suppressed boundaries from the union of spans across
  the whole table (a superset), since a boundary that is spanned anywhere is rare to want
  a junction on; **document whichever choice you make** and cover it with the box-drawing
  test in §4.1 item 7. Do not silently ship junction artifacts.


---

## 4. Verification Plan

### 4.1 Automated Test Suites
Add tests to [tests/test_vistab.py](file:///home/gfariello/VC/vistab/tests/test_vistab.py).
**Assert on exact rendered output or exact structural invariants, not on "does not
crash."** Vague assertions (`assertIn("x", out)`) let a half-correct implementation pass;
these tests must fail if geometry is off by even one character. Each test below states the
precise thing to assert.

1. **Header Spans (exact render):** build a small table with `set_header(["A",
   ColSpan("BC", 2), "D"])`; assert the rendered header line contains `BC` centered
   inside a field of width `_span_block_width(1, 2)` and that there is **no** vertical
   rule character between the two spanned columns on the header line (split the line and
   check the interior positions). Also assert the top border above the span contains the
   plain horizontal char, not a `┬`, at the suppressed boundary (F11 / §3.9a).
2. **Data Spans (adjacency invariant):** after `set_cell_span(0, 1, 3)`, assert
   `len(rows[0]) == row_size`, `rows[0][1].colspan == 3`, and `rows[0][2]` and
   `rows[0][3]` are `VistabPlaceholderCell` with `.source_cell is rows[0][1]`.
3. **Width Distribution (sums exactly):** put a value longer than the natural combined
   width into a spanned cell; assert that after `_compute_cols_width`,
   `_span_block_width(c, k) >= len(value)` AND the covered columns' widths sum to exactly
   the distributed target (no rounding drift — proves the `divmod` distribution in §3.5).
4. **Sorting Interaction (adjacency preserved):** span a cell, call `sort_by(...)`, render,
   then re-assert the adjacency invariant from test 2 holds on the moved row, and that the
   spanned value still renders as one merged block.
5. **Styling on span source:** apply `set_cell_style` to the span's source coordinate and
   assert the ANSI wrap appears once around the merged block; apply zebra styling and
   assert the placeholder columns do not introduce a second, mismatched style run (§5.3).
6. **Backward-compat golden (REQUIRED, Definition of Done §0.3):** render a representative
   no-span table and assert it equals a stored golden string captured from `main`.
   This is the guard that the object-migration did not change existing output.
7. **Box-drawing integrity (REQUIRED, F11):** render a table with a header colspan and a
   data colspan under `style="light"` (Unicode box). Assert that on every horizontal rule,
   no junction glyph (`┬ ┼ ┴ ╦ ╬ ╩` etc.) appears at a column boundary interior to a span,
   and that corners/junctions at real (unspanned) boundaries are unchanged from a no-span
   table of the same shape.

### 4.2 Manual Verification
Create a script `examples/colspan_demo.py` to print a demo table illustrating:
- Multi-column headers for subcategories.
- Wide text values spanning across data rows.
- Verification that Unicode box-drawing lines correctly align around spanned blocks.

---

## 5. Open Questions & Cross-Cutting Constraints (added by plan review)

These are correctness constraints the implementer MUST satisfy. They are not deferrals;
each has a concrete required action. They are grouped here because they cut across
several of the Section 3 subsections.

### 5.1 Parallel physical-length lists in `_draw_line` / `_splitit` (BLOCKER)
`_draw_line` iterates `zip(line, self._width, self._align)`
([src/vistab.py:2523](file:///home/gfariello/VC/vistab/src/vistab.py)) and `_splitit`
iterates `zip(line, self._width)` ([src/vistab.py:2618](file:///home/gfariello/VC/vistab/src/vistab.py)).
Both assume a strict 1:1 mapping of physical cell -> width -> align. The new colspan
loops (3.8/3.9) advance by `colspan`, so they can no longer rely on `zip` over the
physical-length `self._width`/`self._align`/`self._valign`/`self._header_align` lists.
Required: index those lists explicitly by `col_idx` (and, for a span, combine
`self._width[col_idx:col_idx+colspan]`), and derive alignment from the **source** cell's
starting column. Also note the outer `for i in range(self.vislen(line[0]))` loop
([src/vistab.py:2517](file:///home/gfariello/VC/vistab/src/vistab.py)) assumes every
column has the same wrapped line-count; placeholders appended as `[]` (3.8) must be
padded to that same count so `cell[i]` never raises `IndexError`.

### 5.2 ANSI sanitization across a spanned block (BLOCKER, security)
`_draw_line` runs `_sanitize_destructive_ansi` and `_reassert_ansi_context` per physical
column ([src/vistab.py:2534-2539](file:///home/gfariello/VC/vistab/src/vistab.py)). The
span rendering path must apply the exact same sanitization to the merged cell content;
skipping it because the block spans multiple physical columns would reopen the terminal
display-hijack vector that `sanitize_ansi` exists to close (FUNCTIONAL_SPEC §12).
Required: sanitize the rendered span content once, identically to the single-cell path.

### 5.3 Alternating (zebra) styling parity (MEDIUM)
`_get_active_ansi_wrap` selects alternating column styling via `col_idx % 2`
([src/vistab.py:1341](file:///home/gfariello/VC/vistab/src/vistab.py)). When a span
collapses physical columns, the parity/coordinate that styling keys off can drift, and
the styling of the *covered* (placeholder) columns is undefined. Required: define the
rule explicitly — the span block adopts the style of its **source** (starting) physical
column, and placeholder columns contribute no independent style. Document this so the
behavior is intuitive rather than accidental.

### 5.4 `_max_width` shrink can violate a span's minimum (MEDIUM)
The width-distribution in 3.5 adds to `self._width[j]`, but the `_max_width`
redistribution loop ([src/vistab.py:2320-2340](file:///home/gfariello/VC/vistab/src/vistab.py))
reallocates widths without knowledge of spans and may shrink columns below the spanned
cell's minimum content width, producing a negative `fill` / overflow. Required: run span
width distribution **after** the `_max_width` shrink, or feed span minimums into the
shrink so a spanned block's combined width is respected (or explicitly clip via the
existing `on_wrap_conflict` policy and document it).

### 5.5 Specification sync (MEDIUM, contract)
`ColSpan`, `set_header_span`, and `set_cell_span` are user-visible additions.
`FUNCTIONAL_SPEC.md` requires additions to "preserve backward compatibility" and to be
documented. Required: update `FUNCTIONAL_SPEC.md` (and `docs/API.md` if present) to
describe the new public surface, and add a `CHANGELOG.md` entry. This is part of "done,"
not optional follow-up.

### 5.6 Test-list numbering (LOW)
Section 4.1 lists five items; references elsewhere ("Test 4.1-item-4") mean the
**Sorting Interaction** item. Kept as-is for now; renumber if the list is reordered.
