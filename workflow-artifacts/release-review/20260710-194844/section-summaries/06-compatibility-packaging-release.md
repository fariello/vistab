# Section 6 — Compatibility / Packaging / Release (per-phase report)
## What I did
Reviewed packaging (pyproject valid: setuptools, py-modules, console script, [cjk]/[dev] extras) and CI (test.yml matrix ubuntu+windows × py3.9-3.13 + pytest; secret-scan.yml gitleaks full-history). Confirmed src parses; verified the code is syntactically 3.7-compatible (typing.Optional/Union, guarded tomllib/tomli) so requires-python>=3.7 is defensible but untested below 3.9. Assessed compatibility: this release is backward-compatible (colspan/CLI-verbs additive; apply_theme retained as deprecated alias). Assessed schemas: no formal schemas; implicit contracts (themes.json, .vistab.toml, CSV) handled defensively, no drift.
## Why
Operator/stakeholder + engineer lens: can it be installed/run and shipped without breaking users?
## Findings raised
- S6-CI1 (Low): requires-python 3.7 vs CI floor 3.9 — align in S7.
- S6-P1 (completed): packaging valid/buildable.
- (Reinforces S1-BUG1: version bump to 1.2.0 is the key release prerequisite.)
## Considered but did NOT do
- Did NOT add CI (already strong); a type-check gate would be noisy given loose hints (S1-Q1) — not recommended.
- Did NOT run `python -m build` (build tool not installed; pyproject validity confirmed via tomllib parse + ast parse instead — noted as the lighter verification).
