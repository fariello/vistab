# Decisions & assumptions - assess documentation (opencode run)

## Concern / scope
- Concern: **documentation** (README, API, CLI, SPEC, TODO, CHANGELOG, docstrings).
- Scope: whole project docs, verified against `src/vistab.py` (v1.1.3) and `pyproject.toml`.
- This is an **independent second pass** after a prior Gemini `assess documentation` run
  (`.agents/plans/pending/20260709-assess-documentation.md`).

## Project conventions discovered
- Lib + CLI, PyPI-published (`pip install vistab`, `vistab[cjk]`, console script
  `vistab:main`), version 1.1.3.
- No `GUIDING_PRINCIPLES.md` -> universal fallback (honest docs, KISS, intuitive).
- Plan lifecycle `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- CHANGELOG uses Keep-a-Changelog; colspan correctly under `[Unreleased]`.

## Key decisions
- **Verdict "needs work":** docs are broad and mostly correct, but contain first-use
  inaccuracies (dead CLI flags D1, wrong sort axis D2, deprecated-API-as-primary D3/D4).
- **Superset, not replacement:** wrote a separate IPD file
  (`...-assess-documentation-opencode.md`) rather than overwriting Gemini's, and explicitly
  cross-referenced its DOC-IDs. Recommended reconciliation (merge/execute superset) as an
  open question rather than silently deleting the prior plan.
- **Fix-by-default, no deferrals:** every finding is Low Remediation Risk (doc/text edits,
  plus a behavior-neutral internal swap of a deprecated call).
- **Accuracy before completeness before polish:** ordered the plan D1-D7 (accuracy),
  D8 (completeness), D9 (polish), per the documentation lens.

## What I intentionally did NOT propose (and why)
- No rewrite of the README's tone wholesale (only high-traffic sections tightened) —
  Complexity axis; a full rewrite is bloat and out of scope.
- Did **not** re-flag the colspan API docs as inaccurate: verified the colspan usability
  hardening was **implemented** (commit 1203449), so `docs/API.md` lines 53-60 are now
  correct. Flagging them would have been a false positive.
- No new documentation artifacts (tutorials, site) — not warranted for this project size.

## Verified positives (not findings)
- README styles and themes all resolve; all API.md methods exist; all `examples/*.py` run
  clean; packaging supports the documented install commands.

## Post-run corrections
- **FUNCTIONAL_SPEC.md correction:** the report/evidence implied SPEC referenced themes
  cleanly, but `FUNCTIONAL_SPEC.md:29` does contain `apply_theme` (the Gemini pass had this
  right). The `apply_theme -> set_theme` sweep must include `FUNCTIONAL_SPEC.md`.
- **Merged:** this run's IPD and the Gemini run's IPD were merged into
  `.agents/plans/pending/20260709-assess-documentation-merged.md`; both source IPDs removed.

## Open questions for the user
1. Reconcile with the earlier documentation IPD (recommend: execute this superset).
2. Regenerate the `--show-code` gold-master fixture from the corrected generator vs hand-edit.
3. Version-in-docs policy: hard version string vs version-agnostic title (recommend agnostic).
