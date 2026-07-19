# IPD: draw() on an empty table returns None, violating its documented `-> str` contract

- Date: 2026-07-19
- Concern: bugs / correctness (API contract)
- Scope: `Vistab.draw()` empty-table return value in `src/vistab.py`, plus the doc/annotation
  that describes its contract, at v1.2.1. Narrow: one return path and its documentation.
- Status: executed
- Approval: approved by maintainer 2026-07-19
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): discovered while probing degenerate
- 2026-07-19 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-E1..PR-E3. Verified every evidence claim against code (draw() bare return :2216-2217, annotation :2206, docstring :2211, API.md:234 '-> str', CLI guard :4466-4467, demo concat :3596, no Vistab dunder depends on draw()); reproduced None + stream()==[]. Fixes: PR-E1 resolved the dangling 'remove Optional import if unused' to a definitive keep (Optional used in ~dozens of signatures); PR-E2 named the anti-regression invariant (only the empty branch changes; 155 tests + zero fixture diff); PR-E3 added the downstream-safety check (demo concat now safe, CLI 'if drawn:' still prints nothing) and a test that a present-but-empty structure STILL draws a box. Open question resolved with human: return ''; also resolved the review question 'how to draw an empty box' (present-but-empty structure, already works) and required it be documented + pinned. Status -> reviewed.
- 2026-07-19 approved (maintainer): human GO to execute (return '' for empty []); Status -> approved.
- 2026-07-19 executed (its_direct/pt3-claude-opus-4.8-1m-us): draw() empty-table branch returns '' (annotation -> str, docstring updated); TestEmptyTableDraw added (Vistab().draw()=='' as str; ['']/set_header([''])/[None] still draw the one-cell box). docs/API.md + CHANGELOG [Unreleased] Fixed synced. Suite 155 -> 157 green (unittest + pytest), zero fixture changes; build + twine PASS. Status -> executed.
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

Plan-review verification (2026-07-19): every evidence claim above was checked against the code:
`draw()` bare return at src/vistab.py:2216-2217, annotation `-> Optional[str]` at :2206, docstring
at :2211; `docs/API.md:234` says `draw() -> str`; the CLI guard `drawn = table.draw(); if drawn:
print(drawn)` at src/vistab.py:4466-4467; the demo concat `f"{...draw()}..."` at :3596; `draw()`
returns `None` and `stream()` on empty yields `[]` (reproduced). No `__str__`/`__repr__` is defined
on `Vistab` (the two `__str__` at :331 and :652 belong to VistabCell and an exception class and do
not call `draw()`), so no dunder depends on the `None` return; `str(table)` uses default repr and is
unaffected.

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | E1 | In `draw()`, change the empty-table early return from a bare `return` (None) to `return ""`. Update the annotation `def draw(self) -> Optional[str]:` (src/vistab.py:2206) to `-> str` and the docstring line "Returns None if there is no data to draw." (src/vistab.py:2211) to state it returns an empty string for an empty table. Do NOT remove the `from typing import ... Optional ...` import (src/vistab.py:97): plan-review verified `Optional` is used in ~dozens of other signatures (constructors at :293, :882, etc.), so it stays. Touch ONLY the `draw()` early-return + its signature/docstring. | src/vistab.py (`draw()` early return :2216-2217 + signature :2206 + docstring :2211) | Low | New API test: `Vistab().draw() == ""` (a `str`); `print(Vistab().draw())` prints a blank line, not `None`; existing suite stays green. |
| 2 | E1 | Simplify the CLI guard now that `draw()` never returns None: `drawn = table.draw(); if drawn: print(drawn)` still works correctly (`""` is falsy, so an empty table prints nothing) - keep it, but add a one-line comment that `""` is the empty-table sentinel, OR leave untouched. Do NOT change CLI empty-input behavior (it already exits 1 with guidance via a separate path; this branch is for a constructed-empty table). | src/vistab.py (CLI print site) | Low | CLI behavior unchanged: piping empty input still exits 1 with guidance (existing `TestEmptyInputExit` stays green); no new output for an empty constructed table. |
| 3 | E1 | Add the corrected characterization tests: (a) `Vistab().draw()` returns `""` (type `str`) - the case the tests IPD T5 deferred; and (b) an anti-regression assertion that a present-but-empty structure STILL draws a box (`Vistab(style="light").set_header([""]).draw()` and `Vistab(header=False).add_row([""]).draw()` each produce the 3-line `┌──┐/│  │/└──┘`), so the truly-empty-vs-empty-box distinction is pinned. Place with the other degenerate-shape tests (coordinate with the tests IPD so it is not duplicated). | tests/test_vistab.py | Low | Tests pass; (a) return type `str` and value `""`; (b) empty-box render unchanged (byte-exact). |

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
- Anti-regression invariant (rubric D): ONLY the empty-table return path changes. Every NON-empty
  table's rendered output must be byte-identical. Mapped to the existing suite: all 155 tests
  (unittest + pytest) stay green with ZERO fixture changes; a fixture diff would mean this touched
  a non-empty path and is a regression to investigate, not to accept.
- Downstream-safety check (rubric E): the demo concat `f"{...draw()}..."` (src/vistab.py:3596) is
  now provably safe for empty tables (it would previously have raised on a `None`); and the CLI
  guard `if drawn:` (src/vistab.py:4466-4467) still prints NOTHING for a constructed-empty table
  (`""` is falsy). No CLI empty-INPUT behavior changes (that path exits 1 via a separate branch;
  `TestEmptyInputExit` must stay green).
- `python -m unittest discover tests/` and `pytest -q` green; paste the ACTUAL runner output.
- No fixture changes (no rendered non-empty output changes; only the empty-table return value).
- No em/en dashes.

## Spec / documentation sync

- Update `docs/API.md` `draw() -> str` entry to note empty-table returns `""` (it already says
  `-> str`, so the code is being brought INTO line with the doc; add the empty-table clause), AND
  add a one-line "to draw an empty box, give the table a present-but-empty structure, e.g.
  `Vistab().set_header([""])` or `add_row([""])`" note so the truly-empty-vs-empty-box distinction
  is documented (from the review question).
- Update the `draw()` docstring in `src/vistab.py`.
- CHANGELOG `[Unreleased]` Fixed entry: "`draw()` now returns an empty string instead of `None`
  for an empty table, matching its documented `-> str` contract."

## Cross-plan coordination

- Tests IPD `20260719-1530-01` (finding T5, Step 5) deferred the empty-table case pending this
  fix. Sequence: execute THIS IPD first (or together), then T5's empty-table assertion pins
  `draw() == ""` (the corrected behavior) instead of the suspect `None`. If executed together,
  the empty-table test lives in one place, not both.

## Open questions

- Empty-table return: RESOLVED (human, 2026-07-19 plan-review) -> **return `""`**. A table with NO
  header and NO rows has no columns and no rows, so there is genuinely nothing to draw; `""` is the
  correct "nothing in, nothing out" result. It matches `stream()` -> `[]` and the documented
  `-> str` contract, and makes `print(t.draw())` print a blank line rather than the literal `None`.
  Rejected alternatives: a rendered placeholder (scope creep - see the "how to draw an empty box"
  note below, which already works via a present-but-empty structure), and keeping `None` with a doc
  downgrade to `Optional[str]` (`None` is the footgun the CLI already guards against).

- "What if someone WANTS an empty box?" (raised at review) - RESOLVED, no new API needed. An empty
  box is a table with a PRESENT but empty structure, not a truly empty table, and it already renders
  correctly today (verified at review):
  - `Vistab(style="light").set_header([""]).draw()` -> `┌──┐` / `│  │` / `└──┘`
  - `Vistab(header=False).add_row([""]).draw()` -> the same box.
  So the contract is a clean, intuitive split: an empty structure (`Vistab().draw()`) yields `""`;
  a present one-empty-cell structure yields a drawn box. This IPD must PRESERVE the existing empty-box
  rendering (it only touches the no-header-and-no-rows branch), and the doc/CHANGELOG (Step / Spec
  sync below) should state how to draw an empty box so users are not left guessing.

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
