# IPD: Assess self-documentation - minor in-product clarity nits

- Date: 2026-07-19
- Concern: self-documentation (learn-as-you-go / in-product clarity)
- Scope: whole product surface (CLI help/usage/errors/first-run, library docstrings and
  error messages)
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): /assess self-documentation; proposed 2 changes.
- 2026-07-19 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-S1..PR-S2. Verified S1/S2 claims; discovered FUNCTIONAL_SPEC.md:46 already mandates exit 1 on an empty pipe, so S1 is a SPEC-conformance fix (severity Low -> Medium, compat concern retracted, exit code resolved to 1); added the exit-code test, cross-plan sequencing note, and an execution contract. Status -> reviewed.

## Goal

Keep vistab learnable while using it, without external docs. The product is already **strong**
here (verified below); this plan proposes two small, low-risk polish items and explicitly
records the many things that are already good so a future assessor does not re-litigate them.

## Project conventions discovered (Step 0)

- Guiding principles: none in repo; universal fallback (intuitive/self-documenting, general-case,
  KISS, honest docs). Prose convention: no em/en dashes.
- Plan lifecycle: `.agents/plans/pending/`, `YYYYMMDD-HHMM-NN-<slug>.md`.
- Stack: single-module pure-Python library + CLI (`src/vistab.py`); library-first framing.
- Lens lead personas: complete novice (primary), UI/UX engineer, power user.

## What is already strong (verified by execution, NOT proposed for change)

- **First-run on a real TTY:** bare `vistab` (no args) prints full usage + verb guide + "provide
  a file or pipe data" + a `--help` tip, and exits 1 (verified under a pty at
  `src/vistab.py:4104-4112`). Correct onboarding.
- **`--help`:** rich, accurate, library-first, with worked command examples and verb guidance.
- **Errors that teach:** unknown `show` subject lists available subjects; unknown theme lists
  all themes + a "run 'vistab show themes'" tip; bad `--align`/`--dtype` name the valid codes and
  (for dtype) explain each. Exemplary.
- **Discoverability:** `--no-color`, `--no-bidi`, `--demo`/`show`/`help` verbs all surface in
  `--help`.
- **Library:** module docstring and class docstring both carry a runnable `from vistab import`
  example; ALL 52 public methods have docstrings; `draw()` documents its `None`-on-empty return.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| S1 | Medium | Low | novice | first-run / errors-that-teach / SPEC conformance | Piped-but-EMPTY stdin (e.g. `printf '' \| vistab`, or an upstream command that produced nothing) exits **0** with NO output and no hint. The helpful "no tabular dataset found" guidance path only triggers when stdin is a TTY (`not sys.stdin.isatty()` routes empty pipes into stream parsing, which draws nothing). This ALSO violates the documented exit contract: `FUNCTIONAL_SPEC.md:46` states "If an empty data pipe is transmitted ... the program exits with code `1`." So the fix is spec CONFORMANCE, not a risky behavior change. Severity raised to Medium (silent failure + spec violation). | src/vistab.py:4100-4112 (stdin gated on `not isatty`; no-data hint gated on the TTY branch); FUNCTIONAL_SPEC.md:46 (promises exit 1) |
| S2 | Low | Low | novice | examples-at-point-of-use | The `Vistab` class docstring's opening prose is generic ("A class that provides functionality for creating and manipulating ASCII tables") before its Example block; a novice doing `help(Vistab)` sees boilerplate first. Minor: lead with the one-line purpose + the runnable snippet, matching the module docstring's framing. | src/vistab.py Vistab class docstring (len ~1137; Example present but below generic prose) |

No Blocker/High/Medium findings. Nothing false or user-blocking was found; the initial
"bare vistab is silent" suspicion was DISPROVED under a real TTY (it was a non-TTY test artifact).

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | S1 | When the resolved input stream yields ZERO rows (piped-but-empty, or an empty file), emit the same "no tabular dataset found ... provide a file or pipe data; see 'vistab --help'" hint to stderr and exit with code **1** (the value FUNCTIONAL_SPEC.md:46 already promises for an empty pipe, and the value the TTY no-data path already uses at src/vistab.py:4112), instead of a silent exit 0. Keep the successful-render and TTY-no-args paths unchanged. This aligns code to the SPEC; no separate spec edit is needed for exit semantics (but see cross-plan note). | src/vistab.py (stream/no-data handling near 4100-4112 and the stream-exhaust path) | Low | `printf '' \| vistab` prints the no-data hint on stderr and exits **1**; a normal piped table still renders and exits 0 (regression). Add a CLI test asserting both exit codes. |
| 2 | S2 | Reorder/trim the `Vistab` class docstring so the first line states the purpose and a runnable `from vistab import Vistab; ...; print(t.draw())` snippet appears near the top (mirror the module docstring). No API change. | src/vistab.py Vistab class docstring | Low | `help(Vistab)` / `Vistab.__doc__` opens with purpose + example; docstring still valid. |

## Deferred / out of scope (with reason)

None deferred. Both findings are Low Remediation Risk. Nothing dropped.

## Scope check

- Over-scope: none. Resisted proposing interactive prompts, a REPL, or colorized first-run
  tutorials; the product already teaches well (KISS/Complexity axis).
- Under-scope: the empty-input hint (S1) is the one genuine in-product gap; proposed.

## Required tests / validation

- New CLI test: empty stdin (`input=""`) -> stderr contains the no-data guidance, non-zero exit;
  non-empty stdin still renders and exits 0.
- Behavior parity: TTY-no-args path and successful renders unchanged (existing CLI tests green).
- `help(Vistab)` opens with purpose + runnable example (S2).
- Full suite green; no em/en dashes introduced.

## Spec / documentation sync

S1 aligns empty-input behavior to `FUNCTIONAL_SPEC.md:46` (which already promises exit 1 +
implies a message): add a `CHANGELOG.md` **Fixed** entry ("empty input now exits 1 with a
guidance message, matching the documented exit semantics"). No FUNCTIONAL_SPEC edit is needed
for exit semantics (the spec is already correct; the code was wrong); if `docs/CLI.md` gains an
exit-code section (it documents exit 0/2 for verbs at CLI.md:97), add the empty-input exit-1
case there for completeness. S2 is a docstring wording change (no behavior/spec impact).

Cross-plan: the companion documentation IPD
(`.agents/plans/pending/20260719-1408-01-assess-documentation.md`, finding D3) updates the
FUNCTIONAL_SPEC *Public API* section. Its execution should NOT "fix" the exit-semantics line to
match today's buggy exit-0; that line is correct and this S1 makes the code conform. Sequence:
land S1 (code -> exit 1) so the spec's exit-semantics statement becomes true.

## Open questions

- S1 exit code: RESOLVED by plan-review to exit 1 (FUNCTIONAL_SPEC.md:46 already mandates exit 1
  for an empty pipe; the TTY no-data path at src/vistab.py:4112 already exits 1). The original
  "risky backward-compat behavior change" concern is retracted: exit 0 on empty pipe is a
  spec-violating bug, not a contract users may rely on. Remaining sub-question: should an
  empty-but-valid input (header only, zero DATA rows) also hint, or
  only truly-empty input; recommend hinting only when there is no parseable row at all, so a
  legitimate header-only render is unaffected.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution; it is NOT
auto-executed.

1. Review (optionally `/plan-review`, which sets `Status: reviewed`); update `Status:`
   (`to-review` -> `reviewed` -> `approved`) with a Workflow-history line at each step.
2. On approval, set `Status: approved` (+ `Approval:` line), make the changes, run validation,
   sync CHANGELOG/CLI docs for S1.
3. Then set the terminal `Status:` and `git mv` this IPD from `.agents/plans/pending/` to
   `.agents/plans/executed/`.

Execution contract (added by plan-review 2026-07-19):
- Scope fence: S1 touches ONLY the CLI no-data path (src/vistab.py near 4100-4112 + the
  stream-exhaust path) to exit 1 with the guidance message; S2 touches ONLY the `Vistab` class
  docstring. No other behavior changes.
- Honesty: when reporting the new CLI test and suite results, paste the ACTUAL runner output
  (e.g. `python -m unittest discover tests/`); never claim an unrun pass.
- Commit path-scoped (`git commit -- <paths>`), never `git add -A`, never push.
- Open question resolved before execution: S1 exit code = 1 (per plan-review, matching
  FUNCTIONAL_SPEC.md:46); the header-only-input sub-question remains for the executor to confirm.
