# Decisions & assumptions - assess documentation

## Concern / scope
- Concern: documentation (repo docs: README, docs/API.md, docs/CLI.md, FUNCTIONAL_SPEC.md,
  CHANGELOG.md, CONTRIBUTING.md, RELEASING.md, examples/).
- Scope: whole project. Version assessed: 1.2.1.
- Lens lead personas: complete novice (README-only) and engineer/operator (API.md / spec).

## Project conventions discovered
- No GUIDING_PRINCIPLES.md; universal fallback principles apply (intuitive, general-case,
  KISS, honest docs). Prose convention: no em/en dashes (AGENTS.md).
- Plan lifecycle: `.agents/plans/pending/`, filenames `YYYYMMDD-HHMM-NN-<slug>.md`.
- CONTRIBUTING.md states every user-facing change belongs in CHANGELOG.
- Single-module pure-Python lib + CLI; dep wcwidth, optional cjkwrap.

## Method
- Verified accuracy by RUNNING, not reading: executed all examples and the README Quick Start.
- Cross-checked the documented public API against the actual `def set_*/add_*/color_*/bold_*`
  set in `src/vistab.py` via grep sweep.
- Checked recent-feature propagation (set_bidi, set_color, F/E dtype codes) across README /
  API.md / CLI.md / FUNCTIONAL_SPEC.
- Checked link/asset resolution and terminology (deprecated apply_theme).

## What was intentionally NOT proposed and why
- No docs restructure, new guides, or tutorials. The docs are adequate; adding bulk would
  violate the KISS/Complexity axis and the lens's "concise and accurate beats long and
  aspirational" guidance. The plan closes concrete gaps only.
- No code/self-documentation changes here; where a rough edge would be better fixed in-product,
  that belongs to the self-documentation lens (assessed separately), not this doc pass.

## Open questions
- D3: is FUNCTIONAL_SPEC meant to enumerate the full public API (it currently reads that way)?
  If it is higher-level by intent, step 5 narrows to capability areas rather than method names.

## Notes
- No inaccuracies that would break a user were found; all findings are completeness/consistency
  or a signature-line default mismatch. Verdict: adequate.
