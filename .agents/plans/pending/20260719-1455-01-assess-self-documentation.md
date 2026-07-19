# IPD: Assess self-documentation - minor in-product clarity nits

- Date: 2026-07-19
- Concern: self-documentation (learn-as-you-go / in-product clarity)
- Scope: whole product surface (CLI help/usage/errors/first-run, library docstrings and
  error messages)
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-19 created (its_direct/pt3-claude-opus-4.8-1m-us): /assess self-documentation; proposed 2 changes.

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
| S1 | Low | Low | novice | first-run / errors-that-teach | Piped-but-EMPTY stdin (e.g. `printf '' \| vistab`, or an upstream command that produced nothing) exits 0 with NO output and no hint. The helpful "no tabular dataset found" guidance path only triggers when stdin is a TTY (`not sys.stdin.isatty()` routes empty pipes into stream parsing, which draws nothing). A user who piped what they thought was data gets silence. | src/vistab.py:4100-4112 (stdin gated on `not isatty`; no-data hint gated on the TTY branch) |
| S2 | Low | Low | novice | examples-at-point-of-use | The `Vistab` class docstring's opening prose is generic ("A class that provides functionality for creating and manipulating ASCII tables") before its Example block; a novice doing `help(Vistab)` sees boilerplate first. Minor: lead with the one-line purpose + the runnable snippet, matching the module docstring's framing. | src/vistab.py Vistab class docstring (len ~1137; Example present but below generic prose) |

No Blocker/High/Medium findings. Nothing false or user-blocking was found; the initial
"bare vistab is silent" suspicion was DISPROVED under a real TTY (it was a non-TTY test artifact).

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | S1 | When the resolved input stream yields ZERO rows (piped-but-empty, or an empty file), emit the same "no tabular dataset found ... provide a file or pipe data; see 'vistab --help'" hint to stderr and exit non-zero, instead of a silent exit 0. Keep the successful-render and TTY-no-args paths unchanged. | src/vistab.py (stream/no-data handling near 4100-4112 and the stream-exhaust path) | Low | `printf '' \| vistab` prints the no-data hint on stderr and exits non-zero; a normal piped table still renders and exits 0 (regression). Add a CLI test. |
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

S1 changes CLI behavior for the empty-input edge case (silent exit 0 -> hint + non-zero exit):
note it in `CHANGELOG.md` under Fixed/Changed and, if `docs/CLI.md` describes exit behavior,
there. S2 is a docstring wording change (no behavior/spec impact).

## Open questions

- S1 exit code: use exit 1 (consistent with the existing TTY no-data path at line 4112)? Assumed
  yes. Confirm that an empty-but-valid input (header only, zero data rows) should ALSO hint, or
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
