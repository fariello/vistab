# IPD: Colspan behavior decisions — mutator strictness & mixed-row alignment

- Date: 2026-07-09
- Concern: ui-ux (behavior/usability of a shipped feature)
- Scope: Two behaviors of the shipped colspan feature in `src/vistab.py` — (B1) `set_cell_span`/`set_header_span` raising when covered cells are non-empty, and (B2) visual misalignment when a plain data row sits under a spanned header. Docs to sync if behavior is confirmed: `docs/API.md`, `README.md`, `FUNCTIONAL_SPEC.md`.
- Status: PENDING (decisions RESOLVED with maintainer 2026-07-09; awaiting execution approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Decisions resolved (2026-07-09).** B1: adopt a **content-merging** model — a new
> `combine` parameter on `set_cell_span`/`set_header_span`, default `" "`, that joins the
> covered non-empty values (loss-less). `combine=""` joins with no separator; any string is
> a custom separator; `combine=None` restores the strict "refuse to overwrite non-empty"
> mode. The joined text is **stored** as the source cell's value. Headers behave
> identically. B2: **document** as a known limitation (option a) and add a `TODO.md` entry
> to reconsider the "try-harder" auto-alignment (option b) later. See the updated Proposed
> Changes below.

## Goal

Resolve two colspan behaviors that were **open questions in the now-executed colspan
usability hardening IPD** (`.agents/plans/executed/20260709-colspan-usability-hardening.md`).
Because that IPD is terminal, these questions are currently **orphaned** — no live plan
tracks them. This IPD exists to force an explicit decision: for each behavior, either
**accept it as intended and document it**, or **soften it**. Neither is a regression of
pre-v1.1.3 functionality (colspan is net-new); both were surfaced during the post-v1.1.3
"did anything break" review. The point is that a shipped feature should not have
undecided, undocumented surprising behavior.

## Project conventions discovered (Step 0)

- **Stack:** single-module pure-Python library + CLI (`src/vistab.py`).
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`; universal fallback — intuitive/
  self-documenting, **no silent failure**, KISS, honest docs.
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **History:** colspan implemented in `a3350b9`, hardened in `1203449`. The hardening added
  transactional validation (overlap/placeholder/non-empty checks) — B1 is a direct product
  of that hardening; its two behaviors were left as Open Questions there.
- **Domain invariant:** the physical grid stays rectangular ($M \times N$); a source cell
  (`colspan>1`) is followed by exactly `colspan-1` placeholders. Any change here must
  preserve that (it is what prevents the render-time `KeyError` the hardening fixed).

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate. Persona = surfacing view.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| B1 | Medium | Low | Power user | Mutator unusable on populated grid | `set_cell_span(row, col, span)` raises `ValueError("Span would overwrite non-empty cell...")` whenever any covered column already holds a non-empty value. On a normally-populated table (the common case), the coordinate mutator therefore always raises unless the user first blanks the covered cells. Correct per "no silent data loss," but arguably surprising: users expect "span these columns, the covered values are subsumed." Undocumented as a hard constraint beyond the one-line API note. | [src/vistab.py:1877-1935](file:///home/gfariello/VC/vistab/src/vistab.py) (raise at 1935) |
| B2 | Low | Low | Novice | Mixed span/plain-row misalignment | When a spanned header sets `_row_size` to the physical column count, a later **plain** data row with that many raw values renders its own column boundaries that do not align under the merged header block (the data row shows interior separators where the header shows a merged cell). Not a crash; a cosmetic/expectation mismatch of the physical-coordinate model. Reproducible (see Appendix). | render path; grid model in [src/vistab.py:1893-1935](file:///home/gfariello/VC/vistab/src/vistab.py) |

## Proposed changes (ordered, validatable)

This IPD proposes a **decision framework**, not a forced code change. Each finding lists
the resolved decision (recorded 2026-07-09). All are Low Remediation Risk.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | B1 | **RESOLVED: content-merging via a `combine` parameter.** Add `combine: Optional[str] = " "` to `set_cell_span` and `set_header_span` (identical on both). Behavior for the covered range `[col_idx, col_idx+colspan)`: (i) collect the non-empty values in left-to-right physical order, **including the source cell's own value first**; (ii) if `combine` is a string, set the source cell's `.value` to those values joined by `combine` (`" "` default; `""` = no separator; any string = custom); empty/`None` covered cells contribute nothing (no doubled/leading/trailing separators); (iii) if `combine is None`, keep the **strict** behavior — raise `ValueError` if any covered cell is non-empty. In all cases the covered columns become blank `VistabPlaceholderCell`s and the grid stays rectangular. Overlap and placeholder-target checks are **unchanged** (still always raise — those are structural, not data, conflicts). Reframe the strict-mode error message to mention the merge option, e.g. *"column N is non-empty and combine=None; pass combine=' ' (or another separator) to merge these values, or clear the cell first."* (Open Q3.) | `src/vistab.py`, `docs/API.md`, `README.md` | Low | Unit tests: default `combine=' '` merges `["Alice","25","Paris"]` span(1,2) -> source value `"25 Paris"`, cols 2 blank placeholder, adjacency invariant holds, `draw()` no `KeyError`; `combine=""` -> `"25Paris"`; `combine=", "` -> `"25, Paris"`; `combine=None` on non-empty -> `ValueError` with the new message; empty covered cells produce no stray separators; identical behavior verified on `set_header_span`. Existing colspan tests stay green. |
| 2 | B2 | **RESOLVED: document as a known limitation now; TODO the auto-align option.** Add to `README.md` §5 / `FUNCTIONAL_SPEC.md` that spans are per-row physical constructs: to align a column group across the whole table, each row must declare the span (now easy and loss-less via `set_cell_span(..., combine=...)` or inline `ColSpan`). Add an aligned multi-row example to `examples/colspan_demo.py`, and a short note on the plain-row caveat. Add a `TODO.md` entry: *"Consider auto-aligning plain rows under spanned headers (option b) — deferred due to ambiguity + rectangular-grid/render-path risk; needs an unambiguous merge rule first."* | `README.md`, `FUNCTIONAL_SPEC.md`, `examples/colspan_demo.py`, `TODO.md` | Low | The demo shows an aligned multi-row spanned table + the caveat; `TODO.md` records the deferred option; reviewer confirms no engine/invariant change. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| B2 option (b) | Medium-High | complexity + functionality | An auto-alignment heuristic for plain rows under a span is ambiguous (no unique mapping of which plain cells merge) and would touch the rectangular-grid invariant and render path that the hardening stabilized. Defer unless a concrete, unambiguous rule is specified. | Separate design IPD if a real use case appears. |

Note: the deferral applies **only** to B2's risky auto-alignment option (now recorded as a
`TODO.md` item). B2's documentation work and all of B1 are proposed for action now.

## Scope check

- **Over-scope:** none. This IPD deliberately does *not* re-open the executed hardening IPD
  or re-implement colspan; it only resolves two leftover decisions.
- **Under-scope:** the executed hardening IPD shipped B1/B2 as behavior with the decisions
  left "open"; nothing currently tracks them. This IPD closes that gap.

## Required tests / validation

- **B1 (`combine`):** new unit tests covering `combine=' '` (default merge), `combine=''`
  (no separator), `combine=', '` (custom), and `combine=None` (strict raise with the new
  message); empty covered cells produce no stray separators; the joined value is stored on
  the source cell (so `str(cell)`/`sort_by` see it); the adjacency invariant holds and
  `draw()` raises no `KeyError`; identical behavior on `set_header_span`.
- **Overlap/placeholder structural checks unchanged:** still raise regardless of `combine`.
- **B2:** `python examples/colspan_demo.py` shows an aligned multi-row spanned table and the
  plain-row caveat; no engine change, so no regression risk there.
- **Regression:** the existing colspan suite (`test_colspan_*`, `test_set_span_api`,
  `test_regression_colspan_support`) stays green; full `python -m pytest` green.

## Spec / documentation sync

- `docs/API.md`: `set_cell_span`/`set_header_span` — document the `combine` parameter
  (default `" "`, `""` no-sep, custom string, `None` = strict raise), the
  source-value-first join order, and the unchanged overlap/placeholder errors.
- `README.md` §5 + `FUNCTIONAL_SPEC.md`: document that spans are per-row physical constructs
  and the plain-row alignment caveat (B2), pointing at `combine=` as the loss-less way to
  align each row.
- `examples/colspan_demo.py`: add an aligned multi-row example.
- `TODO.md`: record the deferred B2 auto-alignment option.
- `CHANGELOG.md` `[Unreleased]`: note the new `combine` parameter on the span mutators.

## Open questions (RESOLVED 2026-07-09)

1. **B1 policy:** RESOLVED — content-merging `combine` parameter (default `" "`), with
   `combine=None` retaining strict no-overwrite. Stored (not draw-time) join; headers
   identical.
2. **B2 policy:** RESOLVED — document as a known limitation now; add a `TODO.md` entry to
   reconsider the auto-alignment option later.
3. **Error message:** RESOLVED — the strict-mode (`combine=None`) `ValueError` will mention
   the `combine=` merge option, not just "clear it first."

## Appendix: reproduction (verified at HEAD)

```python
from vistab import Vistab, ColSpan
t = Vistab(style="light")
t.set_header(["Name", ColSpan("Contact", 2), "Age"])   # _row_size = 4 physical cols
t.add_row(["Alice", ColSpan("a@x", 2), 30])            # spanned data row: aligns
t.add_row(["Bob", "b@y", "555", 40])                   # plain 4-value row: MISALIGNS
print(t.draw())
```
Output (note the `Bob` row's interior separators under the merged `Contact` header — B2):
```
┌───────┬───────────┬─────┐
│ Name  │  Contact  │ Age │
├───────┼───────────┼─────┤
│ Alice │ a@x       │  30 │
├───────┼───────────┼─────┤
│ Bob   │ b@y │ 555 │  40 │
└───────┴─────┴─────┴─────┘
```
And B1:
```python
t2 = Vistab(); t2.set_header(["A","B","C"]); t2.add_row(["1","2","3"])
t2.set_cell_span(0, 0, 2)   # raises ValueError: "Span would overwrite non-empty cell at column 1; clear it first."
```

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Because it centers on two decisions, approval should record the
chosen option per finding (Open Questions 1-2) before any execution. Recommended next steps:

1. Decide B1 and B2 (Open Questions), optionally via `plan-review`.
2. On approval, execute the chosen options, run validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
