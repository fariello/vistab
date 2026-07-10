# IPD: Assess documentation - documentation alignment and warnings cleanup

- Date: 2026-07-09
- Concern: documentation
- Scope: whole project
- Status: PENDING (awaiting human approval; not executed)
- Author: Antigravity

## Goal

Align documentation across README, API, CLI, SPEC, and TODO files to match the current codebase state. Specifically, replace references to deprecated methods (`apply_theme` and `header`) with their correct replacements (`set_theme` and `set_header`), resolve deprecation warnings generated internally by the CLI and examples, and clean up completed roadmap items to ensure the docs reflect the software's exact capabilities today.

## Project conventions discovered (Step 0)

- Guiding principles: N/A
- Pending-plans location/format used: `.agents/plans/pending/20260709-assess-documentation.md`
- Contributor/spec-sync contract: N/A
- Stack / relevant context: Python 3, CLI parsing, regression test harness utilizing gold-master outputs.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| DOC-01 | High | Low | Software Engineer | Code/CLI | The CLI internally invokes deprecated `apply_theme` causing `DeprecationWarning` noise and breaking regression test match baselines unless warnings are silenced. | `src/vistab.py:3643` |
| DOC-02 | Medium | Low | Complete Novice | Docs/API | The API and README docs advertise `apply_theme` as the primary/sole method for applying themes, leaving the correct `set_theme` method completely undocumented. | `docs/API.md:139`, `README.md:289` |
| DOC-03 | Low | Low | Complete Novice | Docs/API | The `Vistab.__init__` docstring claims it calls `self.header()`, which is deprecated, while it actually calls `self.set_header()`. | `src/vistab.py:781` |
| DOC-04 | Medium | Low | Developer / Maintainer | Docs/Roadmap | `TODO.md` lists `Colspan` as a future roadmap item for `v1.2.0`, even though it is already fully implemented, validated, and shipped. | `TODO.md:25` |
| DOC-05 | Low | Low | Software Engineer | Code Generator | CLI `--show-code` prints code that calls deprecated `apply_theme(custom_theme)` instead of `set_theme`. | `src/vistab.py:3757` |
| DOC-06 | Low | Low | Complete Novice | Docs/Version | `docs/API.md` references `v1.1.2` as its title version, while the actual current version of the library is `1.1.3`. | `docs/API.md:3` |

## Proposed changes (ordered, validatable)

Fix by default; each item should be safe, well-scoped, and verifiable. Note the Remediation Risk and the validation for each.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | DOC-01 | Replace `table.apply_theme(args.theme)` with `table.set_theme(args.theme)` in CLI code. | [vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py) | Low | Run CLI tests and verify no DeprecationWarnings are emitted. |
| 2 | DOC-05 | Update `--show-code` generator in `src/vistab.py` to print `set_theme` instead of `apply_theme`. | [vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py) | Low | Run `python src/vistab.py --show-code` and check output. |
| 3 | DOC-02 | Update `docs/API.md`, `README.md`, `FUNCTIONAL_SPEC.md`, tests, and examples to use `set_theme` instead of `apply_theme`. | [API.md](file:///home/gfariello/VC/vistab/docs/API.md), [README.md](file:///home/gfariello/VC/vistab/README.md), [FUNCTIONAL_SPEC.md](file:///home/gfariello/VC/vistab/FUNCTIONAL_SPEC.md), [test_config.py](file:///home/gfariello/VC/vistab/tests/test_config.py), [test_regression.py](file:///home/gfariello/VC/vistab/tests/test_regression.py), [styled_matrix.py](file:///home/gfariello/VC/vistab/examples/styled_matrix.py) | Low | Run `pytest` to ensure all tests pass. |
| 4 | DOC-01, DOC-05 | Update gold-master regression fixture `regression_cli_show_code.txt` to replace `apply_theme` with `set_theme`. | [regression_cli_show_code.txt](file:///home/gfariello/VC/vistab/tests/fixtures/regression_cli_show_code.txt) | Low | Run `pytest tests/test_regression.py` and ensure it passes. |
| 5 | DOC-03 | Update `__init__` docstring to reference `self.set_header()` instead of `self.header()`. | [vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py) | Low | Inspect docstring. |
| 6 | DOC-04 | Remove `Colspan (Target: v1.2.0)` from `TODO.md` roadmap, as it is fully implemented. | [TODO.md](file:///home/gfariello/VC/vistab/TODO.md) | Low | Inspect `TODO.md`. |
| 7 | DOC-06 | Update version header in `docs/API.md` to reference `v1.1.3` (or upcoming release version). | [API.md](file:///home/gfariello/VC/vistab/docs/API.md) | Low | Inspect file. |

## Deferred / out of scope (with reason)

None. All documentation updates are safe and low Remediation Risk.

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): None.
- Under-scope (needed capability missing; propose adding): None.

## Required tests / validation

- **Unit and Regression Tests**: Run `PYTHONPATH=. pytest` (without `-W ignore`) to confirm that:
  1. No `DeprecationWarning` is emitted during normal test and CLI execution.
  2. All theme integration tests and CLI regression matches pass cleanly.
- **Visual Check**: Run the modified examples (e.g., `styled_matrix.py`) to verify correct styling output.

## Spec / documentation sync

Yes, updates directly synchronize code, specs, README, and inline comments to refer to the correct non-deprecated methods.

## Open questions

None.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync specs/docs.
3. Only then move this IPD from the pending dir to the terminal dir per the project's lifecycle convention (canonical: `.agents/plans/pending/` -> `.agents/plans/executed/`). Plan files are named `YYYYMMDD-<slug>.md`.
