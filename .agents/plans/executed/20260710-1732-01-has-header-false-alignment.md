# IPD: Fix `has_header = False` not un-headering row 0 (alignment stays centered)

- Date: 2026-07-10
- Concern: bug fix (functionality / intuitive API)
- Scope: `src/vistab.py` — the `has_header` setter, the `_draw_line` alignment selection, and a regression test in `tests/`. Source bug report: `.agents/prompts/pending/20260710-has-header-false-alignment-bug.md`.
- Status: EXECUTED (shipped in 1.2.0; fix at src/vistab.py align gating + has_header setter; tests in tests/test_vistab.py TestHasHeaderAlignment; CHANGELOG [1.2.0]). Status corrected 2026-07-11 during release-review 20260711-181922 (was a stale "PENDING" line on an already-executed, executed/-located plan).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Make `table.has_header = False` behave as its docstring implies: turn the auto-consumed
row 0 back into an ordinary data row, so it uses the body column alignment (`_align`)
rather than header alignment (`_header_align`, default centered). Today, a table built via
`Vistab(rows)` (no explicit `header=`) silently consumes row 0 into `self._header`; setting
`has_header = False` afterward suppresses the header divider but leaves row 0 rendered with
centered header alignment — verified still-broken at HEAD.

## Project conventions discovered (Step 0)

- **Stack:** single-module lib+CLI (`src/vistab.py`). Guiding principles: universal
  fallback — intuitive/self-documenting, no silent failure, KISS.
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **Verified code sites (current HEAD):**
  - `has_header` setter ([src/vistab.py:1036-1056](file:///home/gfariello/VC/vistab/src/vistab.py)) only does `self._has_header = value` — a no-op for row 0's structure/alignment.
  - Constructor path consumes row 0 into `self._header` via `add_rows(..., header=True)` (default), stored at [src/vistab.py:1860](file:///home/gfariello/VC/vistab/src/vistab.py).
  - Alignment selection: `align = self._header_align[col_idx] if isheader else self._align[col_idx]` ([src/vistab.py:2869](file:///home/gfariello/VC/vistab/src/vistab.py)); header default is `["c"]` ([src/vistab.py:2740](file:///home/gfariello/VC/vistab/src/vistab.py)). Header drawn with `isheader=True` at [src/vistab.py:2114](file:///home/gfariello/VC/vistab/src/vistab.py) and [src/vistab.py:2235](file:///home/gfariello/VC/vistab/src/vistab.py).
- **Domain invariant (critical, colspan era):** `self._header` can now contain
  `VistabCell`/`VistabPlaceholderCell` objects with span metadata; a source cell is followed
  by exactly `colspan-1` placeholders. Any code that **moves the header row into `_rows`**
  must preserve that adjacency or it can reintroduce the render-time `KeyError`/corruption
  class fixed earlier. This is why the fix must be span-aware.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| H1 | High | Low | Power user / novice | Misleading API / functionality | `has_header = False` after `Vistab(rows)` does not un-header row 0; it stays centered while other rows honor `alignment=`. | repro in bug report; [src/vistab.py:1056](file:///home/gfariello/VC/vistab/src/vistab.py), [src/vistab.py:2869](file:///home/gfariello/VC/vistab/src/vistab.py) |
| H2 | Medium | Low | QA | No coverage | No regression test pins header/first-row alignment behavior. | `tests/` has none |

## Design decision (which fix)

Adopt **Fix #1 (honest setter) + Fix #2 (alignment gate) together**; **defer Fix #3**
(don't auto-consume a header when none requested) as a backward-compat behavior change.

- **Fix #1 — honest `has_header` setter.** On `False`: if a header row is currently
  consumed (`self._header`), prepend it back to `self._rows` and clear `self._header`
  (preserving the row's cell objects/spans **as-is** — it is moved whole, so span adjacency
  within the row is inherently preserved). On `True`: if no header is set and rows exist,
  re-consume the current `self._rows[0]` as the header. Idempotent (setting the same value
  twice is a no-op). Round-trip note: `False`→`True` re-consumes *whatever is now row 0*
  (documented; matches the constructor's own "first row becomes header" semantics).
- **Fix #2 — alignment safety net.** At [src/vistab.py:2869](file:///home/gfariello/VC/vistab/src/vistab.py),
  gate on `_has_header`: `align = self._header_align[col_idx] if (isheader and self._has_header) else self._align[col_idx]`. This makes even a still-structurally-header row render with body alignment when `_has_header` is False, covering any path Fix #1 doesn't move.
- **Defer Fix #3** (Remediation Risk Medium-High, functionality axis): changing the
  constructor to not auto-consume row 0 would alter long-standing behavior relied on by
  existing callers and the test suite; that is a separate API-semantics discussion.

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem. Risk | Validation |
|------|--------|--------|-------|-----------|------------|
| 1 | H1 | Rewrite the `has_header` setter: on transition to `False`, move a consumed `self._header` (if truthy) to the front of `self._rows` and set `self._header = []`; on transition to `True`, if `not self._header` and `self._rows`, pop `self._rows[0]` into `self._header`. Guard against redundant sets (only act on actual change). Preserve the row's objects verbatim (span-safe). Update the docstring to state it moves row 0 in/out of the header slot. | `src/vistab.py` | Low | Repro A renders row 0 left-aligned, identical to workarounds B/C; toggling `False`→`True`→`False` is stable; a table with an explicit `header=` iterable is unaffected. |
| 2 | H1 | Gate alignment on `_has_header` at line 2869 (`isheader and self._has_header`). | `src/vistab.py` | Low | Even if a header row remains structurally, `_has_header=False` renders it with `_align`. |
| 3 | H2 | Add regression tests (`tests/test_vistab.py`): (a) `Vistab(rows, alignment="lr"*3)` + `has_header=False` → first row left-aligned (assert the first data line's leading cell is left-, not center-, padded, using wide columns so centering is visible); (b) `header=False` at construction → same; (c) explicit `header=[...]` iterable → header still centered/drawn (no regression); (d) toggle round-trip `False`→`True` restores a header; (e) **colspan-safe:** a table whose row 0 has a `ColSpan`, with `has_header=False`, still `draw()`s without error and the span renders. | `tests/test_vistab.py` | Low | New tests pass; full `python -m pytest` green (96+). |

## Deferred / out of scope

| Finding | Rem. Risk | Axis | Reason |
|---------|-----------|------|--------|
| Fix #3 (constructor auto-consume) | Medium-High | functionality | Behavior change affecting existing callers/tests; needs a deprecation pass. Separate IPD if pursued. |

## Scope check
- Over-scope: none. Fix is confined to the setter + one alignment line + tests.
- Under-scope: the bug report asked for a regression test (Step 3) — included.

## Required tests / validation
Steps 1-3 validations above; plus confirm no existing test regresses (constructor
auto-header, `set_header_align`, colspan header rendering, streaming header path).

## Spec / documentation sync
Behavior of `has_header` becomes correct-per-docstring; update the setter docstring
(Step 1). No separate FUNCTIONAL_SPEC change required (it already implies headers are
optional); add a `CHANGELOG.md` `[Unreleased]` bug-fix line.

## Open questions
1. Round-trip semantics: `False`→`True` re-consumes the *current* row 0 (which may differ
   from the original header if rows changed meanwhile). Assumed acceptable and documented.

## Approval and execution gate
This IPD is authorized for immediate execution by the maintainer (2026-07-10). On
completion, move this IPD and the source bug prompt to their respective `executed/`
directories.
