# IPD: Colspan behavior decisions — mutator strictness & mixed-row alignment

- Date: 2026-07-09
- Concern: ui-ux (behavior/usability of a shipped feature)
- Scope: Two behaviors of the shipped colspan feature in `src/vistab.py` — (B1) `set_cell_span`/`set_header_span` raising when covered cells are non-empty, and (B2) visual misalignment when a plain data row sits under a spanned header. Docs to sync if behavior is confirmed: `docs/API.md`, `README.md`, `FUNCTIONAL_SPEC.md`.
- Status: EXECUTED (colspan mutator strictness + mixed-row alignment decisions implemented and shipped in 1.2.0). Status corrected 2026-07-11 during release-review 20260711-181922 (stale PENDING line on an executed/-located decisions doc).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Plan-review note (revisions applied 2026-07-09).** Re-verified against current HEAD
> (`_apply_span_to_list` now at [src/vistab.py:1893-1943](file:///home/gfariello/VC/vistab/src/vistab.py); the non-empty check is the loop branch at 1932-1935, the source-cell
> construction at 1938-1943). Findings R1-R6 added and addressed. **Most important (R5):**
> the plan's claim that "existing colspan tests stay green" is **false** — `test_set_span_api`
> ([tests/test_vistab.py:331-336](file:///home/gfariello/VC/vistab/tests/test_vistab.py))
> explicitly asserts `set_header_span(0, 2)` *raises* on a populated header, which is exactly
> the default this change flips to a merge; that test **must be updated**. Also added: the
> merged value must actually render/wrap across the block (R1), `combine` bypasses **only**
> the non-empty branch and value-collection happens **after** all structural checks (R2),
> the join must stringify non-string parts and its dtype interaction is documented (R3), a
> type guard for a non-str/non-None `combine` (R4), and a wording fix on B2 (R6).

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
| B2 | Low | Low | Novice | Mixed span/plain-row misalignment | Because each row's spans are independent physical-column constructs, a **plain** data row (no span) renders its own column boundaries that do not align under a merged header/other-row block (interior separators appear where the block is merged). Not a crash; a cosmetic/expectation mismatch of the physical-coordinate model. Reproducible (see Appendix). | render path; grid model in [src/vistab.py:1893-1943](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R1 | High | Low | Testing/QA | Merged value must render/wrap | (Plan-review.) The point of `combine` is that the merged text flows across the widened block. The plan validated only the *stored* value, not that a long merged value **wraps within the span block and does not overflow/misalign**. Added a render+wrap assertion. | Step 1 validation; wrap path `_splitit`/`_span_block_width` |
| R2 | Medium | Low | Architect | Validate-before-merge ordering | (Plan-review.) `combine` must bypass **only** the non-empty branch (1932-1935); structural checks (colspan range, placeholder target, overlap) run first and unchanged, and value-collection/join happens **after** full validation, preserving the transactional no-partial-mutation guarantee. | [src/vistab.py:1893-1943](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R3 | Medium | Low | SWE | Non-string parts + dtype interaction | (Plan-review.) Covered cells may be non-strings (e.g. int `30`); the join must `str(...)` each part. And the merged value is a pre-formatted string, so `set_cols_dtype` no longer applies to it — document. | non-empty test at [src/vistab.py:1933](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R4 | Medium | Low | SWE | `combine` type guard | (Plan-review.) `combine` is `Optional[str]`; a non-str/non-None value (e.g. `0`) should raise `TypeError`, consistent with the project's input-validation contract. | Step 1 |
| R5 | High | Low | Testing/regression | Plan's "tests stay green" is false | (Plan-review.) `test_set_span_api` asserts `set_header_span(0,2)` *raises* on a populated header — exactly the default being flipped to merge. The test **must be updated**, not assumed green. | [tests/test_vistab.py:331-336](file:///home/gfariello/VC/vistab/tests/test_vistab.py) |
| R6 | Low | Low | Novice | B2 wording | (Plan-review.) B2's cause is per-row independent spans, not the header setting `_row_size`; reworded the finding. | this IPD B2 finding |

## Proposed changes (ordered, validatable)

This IPD proposes a **decision framework**, not a forced code change. Each finding lists
the resolved decision (recorded 2026-07-09). All are Low Remediation Risk.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | B1, R2, R3, R4, R5 | **RESOLVED: content-merging via a `combine` parameter.** Add `combine: Optional[str] = " "` to `set_cell_span` and `set_header_span` (identical on both); thread it through to `_apply_span_to_list`. **Type guard (R4):** if `combine` is neither `str` nor `None`, raise `TypeError("combine must be a string or None")`. **Ordering / transactional integrity (R2):** keep the existing validate-first structure at [src/vistab.py:1893-1943](file:///home/gfariello/VC/vistab/src/vistab.py) — the colspan-range/placeholder-target/overlap checks (1894-1930) run **unchanged and first**; `combine` alters **only** the non-empty branch (1932-1935); value collection + join happen **after** the full validation loop passes, in the mutation block (1937-1943), so a rejected call still mutates nothing. **Merge (when `combine` is a str):** collect the covered cells' values left-to-right **including the source cell's own value first**, drop empty/`None` (using the same emptiness test as 1933: `val is None or str(val).strip()==""`), **stringify each remaining part with `str(...)` (R3)**, and join with `combine`; assign that string as the new source cell's `.value` (built at 1938-1939). `combine=""` = no separator; any string = custom; a fully-empty covered range yields just the source value. **Strict mode (`combine is None`):** keep today's raise if any covered cell is non-empty, with the reworded message (Open Q3). Covered columns become blank `VistabPlaceholderCell`s; grid stays rectangular. **dtype note (R3):** the joined value is a pre-formatted string, so per-column `set_cols_dtype` formatting (e.g. float precision) does **not** re-apply to a merged cell — document this. **Existing tests (R5):** `test_set_span_api` ([tests/test_vistab.py:331-336](file:///home/gfariello/VC/vistab/tests/test_vistab.py)) asserts `set_header_span(0,2)` *raises* on a populated header — under the new default it will *merge*. **This test must be updated**: re-point the raise assertion at `combine=None` and add a positive assertion for the default-merge result. Reframe the strict-mode error, e.g. *"column N is non-empty and combine=None; pass combine=' ' (or another separator) to merge these values, or clear the cell first."* | `src/vistab.py`, `docs/API.md`, `README.md`, `tests/test_vistab.py` | Low | Unit tests: default `combine=' '` merges `["Alice","25","Paris"]` span(1,2) -> source value `"25 Paris"`, col 2 blank placeholder, adjacency invariant holds, `draw()` no `KeyError`; `combine=""` -> `"25Paris"`; `combine=", "` -> `"25, Paris"`; non-string covered value (e.g. int `25`) stringifies (R3); `combine=None` on non-empty -> `ValueError` (new message); `combine=0` -> `TypeError` (R4); empty covered cells produce no stray separators; identical on `set_header_span`; **updated `test_set_span_api` reflects merge-by-default + `combine=None` strict (R5)**; overlap/placeholder still raise regardless of `combine`. |
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
  message); a non-string covered value stringifies (R3); `combine=0` raises `TypeError` (R4);
  empty covered cells produce no stray separators; the joined value is stored on the source
  cell (so `str(cell)`/`sort_by` see it); the adjacency invariant holds and `draw()` raises
  no `KeyError`; identical behavior on `set_header_span`.
- **Render + wrap (R1):** after a merge, `draw()` renders the merged value inside the span
  block, and a merged value long enough to exceed the block width **wraps within the block**
  (multi-line) rather than overflowing or reintroducing interior separators. Assert on the
  rendered output, not just the stored `.value`.
- **Updated existing test (R5):** `test_set_span_api` no longer asserts a raise on a
  populated header by default; its raise assertion is re-pointed at `combine=None`, plus a
  positive assertion that the default merges.
- **Overlap/placeholder structural checks unchanged:** still raise regardless of `combine`;
  a rejected call leaves the grid byte-for-byte unchanged (transactional, R2).
- **B2:** `python examples/colspan_demo.py` shows an aligned multi-row spanned table and the
  plain-row caveat; no engine change, so no regression risk there.
- **Regression:** `test_colspan_*` and `test_regression_colspan_support` stay green
  unchanged; `test_set_span_api` stays green **after** the R5 update; full
  `python -m pytest` green (and still warning-free, per the just-executed documentation IPD).

## Spec / documentation sync

- `docs/API.md`: `set_cell_span`/`set_header_span` — document the `combine` parameter
  (default `" "`, `""` no-sep, custom string, `None` = strict raise), the source-value-first
  join order, the `TypeError` on a non-str/non-None `combine` (R4), the note that merged
  cells are pre-formatted strings unaffected by `set_cols_dtype` (R3), and the unchanged
  overlap/placeholder errors.
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
