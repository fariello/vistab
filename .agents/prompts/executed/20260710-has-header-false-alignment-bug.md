# Bug report / fix prompt - `has_header = False` does not un-header row 0 (alignment stays centered)

## Summary

When a `Vistab` is built by passing data via the `rows=` argument **without** an
explicit `header=`, the constructor silently consumes row 0 as the header. If
the caller then sets `table.has_header = False` (intending "row 0 is ordinary
data"), the header divider line is suppressed **but row 0 is still rendered with
header alignment** (default centered / `_header_align`) instead of the body
column alignment (`_align`). So the first data row is centered while every other
row honors the `alignment=` string.

This makes `has_header = False` misleading: it looks like it should turn row 0
back into a normal data row, but it does not affect that row's alignment (nor
move it out of the consumed-header slot).

## Environment

- Repo: `~/VC/vistab`, `src/vistab.py`
- Reproduced with the current working tree on this machine (Python 3.14).

## Minimal reproduction

```python
import vistab
V = vistab.Vistab

rows = [
    [".config",              "10", ".opencode", "8", ".antigravity-server", "7"],
    [".cargo",               "6",  ".mozilla",  "5", ".expo",               "4"],
    [".cookiecutter_replay", "3",  ".idlerc",   "3", ".keras",              "3"],
]

# A) BUG: rows= only, then has_header = False -> row 0 is CENTERED
t = V(rows, alignment="lr" * 3)
t.has_header = False
t.set_decorations(V.BORDER | V.VLINES)
print(t.draw())
```

Observed (row 0 `.config`, `.opencode`, `.antigravity-server` centered; other
rows left-aligned):

```
┌──────────────────────┬────┬───────────┬───┬─────────────────────┬───┐
│       .config        │ 10 │ .opencode │ 8 │ .antigravity-server │ 7 │
│ .cargo               │  6 │ .mozilla  │ 5 │ .expo               │ 4 │
│ .cookiecutter_replay │  3 │ .idlerc   │ 3 │ .keras              │ 3 │
└──────────────────────┴────┴───────────┴───┴─────────────────────┴───┘
```

Expected: row 0 left-aligned like the rest (names left, counts right).

## Two workarounds that DO produce the expected output (proof of root cause)

```python
# B) Tell the constructor there is no header up front:
t = V(rows, alignment="lr" * 3, header=False)
t.set_decorations(V.BORDER | V.VLINES)
print(t.draw())          # row 0 correctly LEFT-aligned

# C) Or force the header alignment to match the body:
t = V(rows, alignment="lr" * 3)
t.set_decorations(V.BORDER | V.VLINES)
t.set_header_align("lr" * 3)
print(t.draw())          # row 0 correctly LEFT-aligned
```

Both B and C were verified to render row 0 left-aligned.

## Root cause (from reading `src/vistab.py`)

1. Constructor, ~lines 860-869: `is_header` defaults to `True`. With only
   `rows=` passed (no `header=`), `add_rows(rows, header=True)` **consumes row 0
   as the header** and stores it in `self._header`. The caller never asked for a
   header, yet row 0 becomes one.
2. `has_header` setter, ~lines 1036-1056: only assigns `self._has_header =
   value`. It does **not** move the already-consumed header row back into
   `self._rows`, and does not change alignment. So flipping it to `False` after
   construction is effectively a no-op for a table built via `rows=`.
3. Cell alignment, ~line 2869:
   `align = self._header_align[col_idx] if isheader else self._align[col_idx]`.
   Row 0 is drawn from `self._header` with `isheader=True` (e.g. the header draw
   sites at ~lines 2114 / 2235), so it uses `_header_align` (default `["c"]`,
   see ~line 2740) regardless of `self._has_header`.

Net: `_has_header` gates the header *divider line* (~lines 2167, and the
`self._deco & Vistab.HEADER` checks) but not (a) whether row 0 was consumed as a
header at construction, nor (b) the alignment applied to that row.

## Suggested fix (design decision needed - see options)

Pick whichever matches intended semantics; all are low-risk:

1. **Make the `has_header` setter honest (preferred).** When set to `False`,
   move the consumed `self._header` row (if any) back to the front of
   `self._rows` and clear `self._header`, so row 0 becomes a normal data row and
   uses `_align`. When set back to `True`, re-consume row 0. This makes
   `has_header` a real toggle post-construction.

2. **Gate the alignment choice on `_has_header`.** At ~line 2869 (and any peer
   sites), use `self._header_align[col_idx] if (isheader and self._has_header)
   else self._align[col_idx]`. Cheaper, but leaves the "row 0 was consumed into
   `_header`" oddity in place (header row still separate structurally).

3. **Don't auto-consume a header when none was requested.** In the constructor,
   only treat row 0 as a header when `header=True` is passed explicitly (or a
   `header=` iterable is given). Passing only `rows=` would default to no header.
   This is the most intuitive API but is a **behavior change** that could affect
   existing callers who rely on the current auto-header-from-first-row behavior,
   so it needs a deprecation/consideration pass.

Recommendation: do (1) so `has_header=False` behaves as its docstring implies
(~lines 1043-1053 say "append raw datasets without wanting headers drawn, set
this to False"), and additionally consider (2) as a cheap safety net. Treat (3)
as a separate API-semantics discussion.

## Acceptance criteria

- Repro A above renders row 0 left-aligned (identical to B and C).
- `has_header = False` set after construction (table built via `rows=`) makes
  row 0 a normal data row: it uses the body `alignment=` for that row and is not
  structurally treated as a header.
- Existing behavior with an explicit `header=` (iterable) is unchanged: that
  header still renders with header alignment/line.
- Add a regression test: build with `rows=` + wide columns so a short first-row
  cell would visibly center under the buggy path; assert the first row is
  left-aligned when `has_header=False` (and when `header=False` at construction).

## Notes

- Discovered while using vistab as a library in `~/VC/linux-config/bin/sup.py`
  to render a multi-column `(name, count)` grid. Current workaround there is
  option C (`set_header_align("lr"*n)`), which is fine, but the surprising part
  is that `has_header = False` alone did nothing to the alignment.
