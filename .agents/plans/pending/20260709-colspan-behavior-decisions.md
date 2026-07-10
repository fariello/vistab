# IPD: Colspan behavior decisions — mutator strictness & mixed-row alignment

- Date: 2026-07-09
- Concern: ui-ux (behavior/usability of a shipped feature)
- Scope: Two behaviors of the shipped colspan feature in `src/vistab.py` — (B1) `set_cell_span`/`set_header_span` raising when covered cells are non-empty, and (B2) visual misalignment when a plain data row sits under a spanned header. Docs to sync if behavior is confirmed: `docs/API.md`, `README.md`, `FUNCTIONAL_SPEC.md`.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

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
the recommended default plus alternatives; the human picks per finding (see Open
Questions). All options are Low Remediation Risk.

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | B1 | **DECISION REQUIRED.** Pick one: **(a) Accept + document (recommended):** keep the raise; add a clear sentence to `docs/API.md` `set_cell_span`/`set_header_span` and README §5 that covered cells must be empty (blank them first) and that this prevents silent data loss; ensure the error message suggests the fix (it already says "clear it first"). **(b) Soften to opt-in overwrite:** add a keyword like `overwrite=False`; when `True`, covered non-empty cells are absorbed silently (documented). **(c) Soften to warn:** downgrade the raise to a `warnings.warn` + absorb. Recommended: (a) — least complexity, preserves the no-silent-loss invariant the hardening was written for. | `docs/API.md`, `README.md` (option a) or `src/vistab.py` (b/c) | Low | Option (a): a doc example spanning over pre-filled cells demonstrates the "clear first" pattern; error message verified. Option (b/c): unit test for the new path + adjacency invariant preserved + no render `KeyError`. |
| 2 | B2 | **DECISION REQUIRED.** Pick one: **(a) Document as a known limitation (recommended):** state in `README.md` §5 / `FUNCTIONAL_SPEC.md` that spans are physical-column constructs and that rows meant to align under a spanned header should themselves declare matching spans/placeholders (or use `ColSpan`); show the aligned pattern in `examples/colspan_demo.py`. **(b) Auto-align heuristic:** attempt to coalesce a plain row's cells under an overhead span — **not recommended** (ambiguous which cells merge; risks the rectangular-grid invariant and the render path; Complexity + Functionality axes). | `README.md`, `FUNCTIONAL_SPEC.md`, `examples/colspan_demo.py` (option a) | Low | Option (a): the demo shows an aligned multi-row spanned table and a note on the plain-row caveat; reviewer confirms no invariant change. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| B2 option (b) | Medium-High | complexity + functionality | An auto-alignment heuristic for plain rows under a span is ambiguous (no unique mapping of which plain cells merge) and would touch the rectangular-grid invariant and render path that the hardening stabilized. Defer unless a concrete, unambiguous rule is specified. | Separate design IPD if a real use case appears. |

Note: the deferral applies **only** to B2's risky option (b). B2's safe option (a,
document) and all of B1 are proposed for action now.

## Scope check

- **Over-scope:** none. This IPD deliberately does *not* re-open the executed hardening IPD
  or re-implement colspan; it only resolves two leftover decisions.
- **Under-scope:** the executed hardening IPD shipped B1/B2 as behavior with the decisions
  left "open"; nothing currently tracks them. This IPD closes that gap.

## Required tests / validation

- If B1 stays as-is (option a): no code change; add/verify the doc example and the
  error-message wording; existing colspan tests remain green.
- If B1 is softened (option b/c): new unit test for the overwrite/warn path; assert the
  adjacency invariant holds and `draw()` does not raise `KeyError`.
- B2 (option a): `python examples/colspan_demo.py` shows an aligned spanned table; docs
  describe the plain-row caveat. No engine change, so `python -m pytest` unaffected.
- Any code option must keep the existing colspan suite (`test_colspan_*`, `test_set_span_api`,
  `test_regression_colspan_support`) green.

## Spec / documentation sync

- `docs/API.md`: `set_cell_span`/`set_header_span` — document the covered-non-empty rule
  (B1) and, if adopted, the `overwrite`/warn option.
- `README.md` §5 + `FUNCTIONAL_SPEC.md`: document the physical-column nature of spans and
  the plain-row alignment caveat (B2).
- `examples/colspan_demo.py`: add an aligned multi-row example.

## Open questions

1. **B1 policy:** accept + document (recommended), add `overwrite=` opt-in, or downgrade to
   a warning?
2. **B2 policy:** document as a known limitation (recommended) or attempt auto-alignment
   (deferred as Medium-High complexity)?
3. Should B1's error, if kept, additionally point at `set_cell_span` requiring empty covered
   cells in the message text (currently "clear it first")?

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
