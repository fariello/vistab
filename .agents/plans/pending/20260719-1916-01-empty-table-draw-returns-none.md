# IPD: draw() on an empty table returns None, violating its documented `-> str` contract

- Date: 2026-07-19
- Concern: bugs / correctness (API contract)
- Scope: `Vistab.draw()` empty-table return value in `src/vistab.py`, plus the doc/annotation
  that describes its contract, at v1.2.1. Narrow: one return path and its documentation.
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): discovered while probing degenerate
  table shapes for the tests IPD (20260719-1530-01, finding T5). `Vistab().draw()` on a table
  with no header and no rows returns `None`, not a string. Filed as a bug-fix IPD to run BEFORE
  the tests IPD so T5 can pin the corrected behavior instead of a known-suspect `None`.

## Goal

Make `draw()` honor its published contract: it should always return a string. On an empty table
(no header, no rows) it currently returns `None`, which contradicts the public API doc and is a
footgun for the ordinary caller `print(table.draw())` and any `table.draw().splitlines()` /
string-concatenation use. Fix it to return the empty string `""`.

## Evidence (measured, not inferred)

- `Vistab().draw()` returns `None`:
  ```
  $ PYTHONPATH=src python -c "from vistab import Vistab; r=Vistab().draw(); print(type(r).__name__)"
  NoneType
  ```
- The cause is deliberate but wrong: `src/vistab.py` `draw()` has, near the top,
  `if not self._header and not self._rows: return` (bare `return`, i.e. `None`). The method is
  annotated `def draw(self) -> Optional[str]:` and its docstring says "Returns None if there is
  no data to draw."
- The PUBLIC contract disagrees: `docs/API.md` documents `### draw() -> str` ("output the final
  multi-line string"), i.e. `str`, not `Optional[str]`. So code and public doc are inconsistent;
  the doc is the promise users read.
- `None` is already treated as a footgun inside the codebase:
  - The CLI defends against it: `src/vistab.py` `drawn = table.draw(); if drawn: print(drawn)`
    (the guard exists precisely because `draw()` can be falsy/None).
  - A demo path concatenates results directly: `f"{t_fg.draw()}\n{t_bg.draw()}\n{t_ts.draw()}"`;
    that pattern would raise if any table were empty.
- Parity: `stream()` on empty input yields `[]` (an empty sequence of lines), the streaming
  analogue of an empty string. `draw()` returning `""` matches that mental model.
- README teaches `print(t.draw())` as the canonical usage; `print(None)` prints the literal
  `None`, a surprising and incorrect result for an empty table.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| E1 | Medium | Low | QA / API-design | contract violation / footgun | `draw()` returns `None` for an empty table (no header, no rows) but the public API doc promises `-> str`. `print(table.draw())` (the documented usage) prints `None`, and `table.draw().splitlines()` / any `+` concatenation raises `AttributeError`/`TypeError`. The codebase already works around it (CLI `if drawn:` guard). | `draw()` bare `return` on empty; `Optional[str]` annotation + docstring vs `docs/API.md` `draw() -> str`; reproduced `type == NoneType` |

No Blocker/High. No data loss. Single, well-understood defect.

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | E1 | In `draw()`, change the empty-table early return from a bare `return` (None) to `return ""`. Update the annotation `def draw(self) -> Optional[str]:` to `-> str` and the docstring line "Returns None if there is no data to draw." to state it returns an empty string for an empty table. Remove the now-unnecessary `Optional` import ONLY if it is unused elsewhere (verify first; do not touch unrelated signatures). | src/vistab.py (`draw()` early return + signature/docstring) | Low | New API test: `Vistab().draw() == ""` (a `str`); `print(Vistab().draw())` prints a blank line, not `None`; existing suite stays green. |
| 2 | E1 | Simplify the CLI guard now that `draw()` never returns None: `drawn = table.draw(); if drawn: print(drawn)` still works correctly (`""` is falsy, so an empty table prints nothing) - keep it, but add a one-line comment that `""` is the empty-table sentinel, OR leave untouched. Do NOT change CLI empty-input behavior (it already exits 1 with guidance via a separate path; this branch is for a constructed-empty table). | src/vistab.py (CLI print site) | Low | CLI behavior unchanged: piping empty input still exits 1 with guidance (existing `TestEmptyInputExit` stays green); no new output for an empty constructed table. |
| 3 | E1 | Add the corrected characterization test for the empty table (this is the case the tests IPD T5 deferred): `Vistab().draw()` returns `""` (type `str`). Place it with the other degenerate-shape tests (coordinate with the tests IPD so it is not duplicated). | tests/test_vistab.py | Low | Test passes; asserts return type is `str` and value is `""`. |

## Deferred / out of scope (with reason)

- No new "empty table renders a placeholder box" feature. Returning `""` matches `stream()` and is
  the least-surprising, smallest fix. A visible "empty table" render would be a feature request,
  not a bug fix, and is explicitly NOT in scope.
- No change to the CLI empty-INPUT path (piped/empty-file), which already exits 1 with guidance
  (self-doc S1). This IPD is only about the library `draw()` return value.

## Scope check

- Over-scope: do not overhaul return types across the API, and do not add an empty-table render
  feature. One return value + its doc/annotation + one test.
- Under-scope: the contract mismatch itself (doc says `str`, code returns `None`) is the real
  defect; fixed here rather than papered over with more caller-side `if drawn:` guards.

## Required tests / validation

- New test: `Vistab().draw() == ""` and `isinstance(Vistab().draw(), str)`.
- `python -m unittest discover tests/` and `pytest -q` green; paste the ACTUAL runner output.
- No fixture changes (no rendered non-empty output changes; only the empty-table return value).
- No em/en dashes.

## Spec / documentation sync

- Update `docs/API.md` `draw() -> str` entry to note empty-table returns `""` (it already says
  `-> str`, so the code is being brought INTO line with the doc; add the empty-table clause).
- Update the `draw()` docstring in `src/vistab.py`.
- CHANGELOG `[Unreleased]` Fixed entry: "`draw()` now returns an empty string instead of `None`
  for an empty table, matching its documented `-> str` contract."

## Cross-plan coordination

- Tests IPD `20260719-1530-01` (finding T5, Step 5) deferred the empty-table case pending this
  fix. Sequence: execute THIS IPD first (or together), then T5's empty-table assertion pins
  `draw() == ""` (the corrected behavior) instead of the suspect `None`. If executed together,
  the empty-table test lives in one place, not both.

## Open questions

- Empty-table return: `""` (recommended, matches `stream()` -> `[]` and the `-> str` doc) vs a
  rendered "(empty)" placeholder (rejected as scope creep) vs keeping `None` but fixing the doc to
  `Optional[str]` (rejected: `None` is the footgun the CLI already guards against, and README
  teaches `print(t.draw())`). Recommend `""`. Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution; it is NOT
auto-executed.

1. Review (optionally `/plan-review`, which sets `Status: reviewed`); confirm the `""` decision.
   Update `Status:` with a Workflow-history line at each step.
2. On approval, set `Status: approved` (+ `Approval:` line), implement, add the test, sync
   API.md/CHANGELOG, run the suite, confirm green.
3. Then set the terminal `Status:` and `git mv` this IPD from `.agents/plans/pending/` to
   `.agents/plans/executed/`.

Execution contract:
- Scope fence: touches ONLY `draw()`'s empty-table return + its signature/docstring, the optional
  CLI-guard comment, one test, and the API.md/CHANGELOG sync. No unrelated refactors.
- Honesty: paste the ACTUAL runner output when reporting the suite result; never claim an unrun
  pass.
- Commit path-scoped (`git commit -- <paths>`), never `git add -A`, never push.
