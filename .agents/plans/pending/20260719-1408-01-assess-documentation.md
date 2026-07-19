# IPD: Assess documentation - accuracy fixes and 1.2.1 completeness gaps

- Date: 2026-07-19
- Concern: documentation
- Scope: whole project (README, docs/API.md, docs/CLI.md, FUNCTIONAL_SPEC.md, CHANGELOG.md,
  CONTRIBUTING.md, RELEASING.md, examples/)
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): /assess documentation; proposed 6 changes.
- 2026-07-19 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-D1..PR-D3. All D1/D2/D4/D5 claims verified against repo evidence; added a cross-plan guard so the FUNCTIONAL_SPEC edit does not corrupt the correct exit-semantics line, a concrete CHANGELOG-Fixed requirement for D1, and an execution contract to the gate. Status -> reviewed.

## Goal

Keep vistab's user-facing documentation accurate and complete for the shipped 1.2.1 surface.
The docs are in good shape (all 3 examples run, ~48 of ~48 public methods largely covered,
links resolve, no stale `apply_theme` recommendations), but a focused pass found a few
low-risk accuracy and completeness gaps, mostly features added in 1.2.0/1.2.1 (RTL bidi,
grouped-number `F`/`E` codes, `set_color`) that never propagated to every doc surface. The
lead personas are the complete novice (who reads only the README) and the engineer/operator
(who relies on API.md / the spec).

## Project conventions discovered (Step 0)

- Guiding principles: none in repo; universal fallback (intuitive/self-documenting,
  general-case, KISS, honest docs). Prose convention: no em/en dashes (AGENTS.md).
- Pending-plans location/format: `.agents/plans/pending/`, `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contributor/spec-sync contract: `CONTRIBUTING.md` (says every user-facing change belongs in
  CHANGELOG), `AGENTS.md`.
- Stack: single-module pure-Python library + CLI (`src/vistab.py`), dep `wcwidth`, optional
  `cjkwrap`. Docs: README + `docs/API.md` + `docs/CLI.md` + `FUNCTIONAL_SPEC.md` + CHANGELOG +
  CONTRIBUTING + RELEASING. Current version 1.2.1.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D1 | Medium | Low | engineer | accuracy | `__init__` signature line documents `header: bool = True`, but the real default is `None` and the type is `Union[bool, Iterable]`. Contradicts the same file's own prose (line 25 correctly says `Union[bool, List[str]]`). Misleads a caller about the default. | docs/API.md:22 vs src/vistab.py `__init__`; API.md:25 |
| D2 | Medium | Low | novice | completeness | README never mentions RTL/`set_bidi` or the grouped-number `F`/`E` dtype codes. A user reading only the README cannot discover two shipped 1.2.x capabilities. | README.md (0 hits for `set_bidi`, `` `F` ``); present only in docs/API.md, docs/CLI.md |
| D3 | Medium | Low | engineer | completeness | `FUNCTIONAL_SPEC.md` "Public API" section predates 1.2.x: no `set_bidi`, `set_color`, or the grouped `F`/`E` dtype codes. The spec no longer fully reflects the surface. | FUNCTIONAL_SPEC.md sec 4 (0 hits for set_bidi/set_color/grouped) |
| D4 | Low | Low | engineer | completeness | Two public methods are undocumented in API.md: `set_header_align` and `set_abnormal_row_style`. | docs/API.md (grep: both absent); src/vistab.py defs |
| D5 | Low | Low | novice | completeness | `docs/CLI.md` does not document the `showcase` subject of `show`/`demo` (it exists and is in the README). CLI reference is incomplete for that verb. | docs/CLI.md (0 hits for `showcase`); README.md has it |
| D6 | Low | Low | engineer | consistency | API.md `__init__` signature omits the `-> None` / `Optional[...]` typing shown in code; minor drift alongside D1 (fold into the D1 fix). | docs/API.md:22 |

Nothing false or dangerous was found: examples run, the README Quick Start runs verbatim,
docs links resolve, terminology is consistent (no deprecated `apply_theme` recommended).

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D1, D6 | Correct the `__init__` doc signature to match code: `header` default `None`, typed `Union[bool, Iterable[Any]]`; keep the accurate line-25 prose. Align the shown signature with the real one. | docs/API.md:22-25 | Low | Signature matches `src/vistab.py` `__init__`; internal consistency with line 25. |
| 2 | D4 | Add API.md entries for `set_header_align(array)` and `set_abnormal_row_style(...)` in the matching sections. | docs/API.md | Low | Every public `set_*`/`color_*`/`bold_*` method appears in API.md (grep sweep). |
| 3 | D2 | Add a short README subsection (or bullets) surfacing RTL bidi (`set_bidi`, correct RTL rendering) and the grouped-number `F`/`E` dtype codes, linking to API.md/CLI.md for detail. Concise, not aspirational. | README.md | Low | README grep finds `set_bidi` and the `F` code; novice can discover both from the README alone. |
| 4 | D5 | Document the `showcase` subject under the `show`/`demo` verbs in CLI.md. | docs/CLI.md | Low | `vistab show showcase` documented; matches actual CLI subjects. |
| 5 | D3 | Update FUNCTIONAL_SPEC.md section 4 (Public API) to include `set_bidi`, `set_color`, and the grouped `F`/`E` dtype codes, and any other 1.2.x additions, so the spec reflects the shipped surface. | FUNCTIONAL_SPEC.md | Low | Spec API list is a superset of the public methods; no shipped public capability missing. |
| 6 | (verification) | After edits, re-run the accuracy checks (examples execute; public-method coverage grep; link/asset existence) to confirm no new drift. | (docs only) | Low | All examples exit 0; coverage grep clean; no broken links. |

## Deferred / out of scope (with reason)

None deferred: every finding is Low Remediation Risk (docs-only edits). No finding was dropped.

## Scope check

- Over-scope: none. Avoided proposing a docs overhaul or new guides; the docs are adequate and
  the plan only closes concrete accuracy/completeness gaps (KISS/Complexity axis).
- Under-scope: the five gaps above are the missing coverage; all are proposed.

## Required tests / validation

- Run each `examples/*.py` under `PYTHONPATH=src`; all must exit 0 and render (accuracy of
  examples).
- Grep sweep: every public `set_*`/`add_*`/`color_*`/`bold_*`/`draw`/`stream`/`sort_by`/`reset`
  method appears in `docs/API.md`.
- Confirm README now contains `set_bidi` and the `F`/`E` codes; CLI.md contains `showcase`;
  FUNCTIONAL_SPEC section 4 lists the 1.2.x additions.
- Link/asset existence check across README + docs/*.md unchanged (no new broken links).
- No em/en dashes introduced (repo convention).

## Spec / documentation sync

This plan IS documentation sync. It changes no code and no behavior, so no code/test changes
are required. It brings FUNCTIONAL_SPEC and the reference docs in line with shipped 1.2.1.

CHANGELOG: add a brief `[Unreleased]`/next-version **Fixed** note that the docs corrected a
documented-API inaccuracy (the `__init__` `header` default/type, D1), since CONTRIBUTING requires
user-facing changes in the CHANGELOG and D1 corrects previously-shipped reference documentation.
The pure additions (D2/D4/D5 new sections, D3 spec fill-in) do not each need a CHANGELOG line.

## Open questions

- D3 (FUNCTIONAL_SPEC): confirm the spec is meant to enumerate the full public API surface
  (it currently reads that way). If the spec is intended as higher-level only, step 5 narrows
  to just noting the capability areas rather than the method list.

- Cross-plan (added by plan-review 2026-07-19): while editing FUNCTIONAL_SPEC (D3, step 5) do
  NOT touch the Exit Semantics line (`FUNCTIONAL_SPEC.md:46`), which states an empty pipe exits
  `1`. That statement is CORRECT and intended; the current code wrongly exits `0`, and the
  companion self-documentation IPD
  (`.agents/plans/pending/20260719-1455-01-assess-self-documentation.md`, finding S1) fixes the
  code to conform. Do not "reconcile" the spec down to the buggy behavior. This D3 edit is
  scoped to the *Public API* section (section 4) only.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed.

1. Review (optionally `/plan-review`, which sets `Status: reviewed`); update `Status:`
   (`to-review` -> `reviewed` -> `approved`) with a Workflow-history line at each step.
2. On approval, set `Status: approved` (+ `Approval:` line), make the ordered doc edits, run
   the validation, and (since this is docs-only) add a CHANGELOG note only if any wording
   corrects a previously-shipped inaccuracy.
3. Then set the terminal `Status:` and `git mv` this IPD from `.agents/plans/pending/` to
   `.agents/plans/executed/`.

Execution contract (added by plan-review 2026-07-19):
- Scope fence: this plan edits ONLY the named docs (README, docs/API.md, docs/CLI.md,
  FUNCTIONAL_SPEC.md section 4, and a CHANGELOG note). No source/test/behavior changes. Do NOT
  touch FUNCTIONAL_SPEC.md:46 Exit Semantics (see the cross-plan open question).
- Honesty: when reporting that validation ran (examples execute, coverage grep, link check),
  paste the ACTUAL command output; never claim a check you did not run.
- Commit path-scoped (`git commit -- <paths>`), never `git add -A`, never push.
- Open questions resolved before execution: the D3 spec-scope question and the cross-plan
  exit-semantics note.
