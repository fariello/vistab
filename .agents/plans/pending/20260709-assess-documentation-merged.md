# IPD: Assess documentation - accuracy sweep & deprecation cleanup (merged)

- Date: 2026-07-09
- Concern: documentation
- Scope: whole project docs — `README.md`, `docs/API.md`, `docs/CLI.md`, `FUNCTIONAL_SPEC.md`, `TODO.md`, `CHANGELOG.md`, inline docstrings, and the CLI code paths that emit/generate docs-by-example. Verified against `src/vistab.py` (v1.1.3) and packaging.
- Status: PENDING (awaiting human approval; not executed)
- Author: merged from two `assess documentation` runs — Antigravity/Gemini (`20260709-assess-documentation.md`) and opencode (`20260709-assess-documentation-opencode.md`).

> **Provenance / merge note.** Two independent documentation assessments were run. The
> opencode pass was a strict **superset** of the Gemini pass on findings (all six Gemini
> findings reproduced) and added three the Gemini pass missed — including the two
> highest-harm CLI-doc bugs (dead flags, wrong `--sort-by` axis). The Gemini pass
> contributed **better execution sequencing** for the `apply_theme -> set_theme` swap (a
> dedicated fixture-regeneration step that prevents a mid-sweep regression failure) and one
> precise evidence point (`FUNCTIONAL_SPEC.md:29` contains `apply_theme`). This IPD merges
> both: the superset findings, ordered accuracy-first, with Gemini's fixture-safe
> sequencing for the theme swap. The two source IPDs are superseded by this file.
> Finding-ID map: `D1,D2,D8,D9` are new (opencode); `D3=DOC-02, D4=DOC-01/05, D5=DOC-04,
> D6=DOC-06, D7=DOC-03`.

## Goal

Make every user-facing doc describe what `vistab` actually does **today**, so a novice
following the README/CLI docs reaches a first success without hitting a command or method
that errors, and a maintainer can trust the API reference. Eliminate deprecated-API
noise (`apply_theme`/`header`) from docs, examples, generated code, and internal calls.
Documentation-lens priority: **fix inaccuracies first** (highest harm), then fill small
gaps, then light polish; keep it concise (no bloat).

## Project conventions discovered (Step 0)

- **Intent / audience / stack:** `vistab` is a lightweight pure-Python terminal-table
  library **and** CLI (`src/vistab.py`, v1.1.3 per `pyproject.toml`), published to PyPI
  (`pip install vistab`, console script `vistab = "vistab:main"`, optional `[cjk]` extra).
  Audience: Python developers and CLI users; docs are the primary onboarding surface.
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`; universal fallback — **honest docs
  over impressive docs**, intuitive/self-documenting, KISS.
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **Contributor/spec-sync contract:** `AGENTS.md` (workflow index only). `CHANGELOG.md`
  follows Keep-a-Changelog; colspan is correctly under `[Unreleased]`.
- **Test harness:** `tests/test_regression.py` uses gold-master fixtures (e.g.
  `tests/fixtures/regression_cli_show_code.txt`) — any change to `--show-code` output must
  regenerate the matching fixture in the same step.
- **Scope exclusions:** `.agents/workflows/` and `workflow-artifacts/` are not assessed.
- **Positive baseline (verified; do NOT "fix"):** README styles (`round-header`, `round`,
  `light`, `ascii`, `none`) and themes (`ocean`, `forest`, `graphite`, `orchid`,
  `sunflower`, `ocean-rows-index`) all exist; all `docs/API.md`-listed methods exist; all
  three `examples/*.py` run clean; the colspan usability hardening was implemented (commit
  `1203449`), so the `docs/API.md` colspan section (lines 53-60) is accurate.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate. Persona = surfacing view.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D1 | High | Low | Novice / operator | CLI docs (dead flags) | `docs/CLI.md` documents diagnostic flags `-M`, `-L`, `-C` (lines 74-76), which **no longer exist**; the CLI uses `--demo {styles,colors,capabilities,anatomy,themes}` (as the README already does). A user following CLI.md's diagnostics gets an error. | [docs/CLI.md:74-76](file:///home/gfariello/VC/vistab/docs/CLI.md); [src/vistab.py:3332](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D2 | Medium | Low | Novice | CLI docs (wrong semantics) | `docs/CLI.md:44` describes `--sort-by INDEX` as "a specified **row** index," but it is a **column** index (the CLI help string says "Column index (0-indexed)"). | [docs/CLI.md:44](file:///home/gfariello/VC/vistab/docs/CLI.md); [src/vistab.py:3339](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D3 | Medium | Low | Novice / SWE | Deprecated API as primary (= DOC-02) | README (Custom Themes) and `docs/API.md` §6 present `apply_theme` as the primary theming method; the non-deprecated `set_theme` is undocumented. `apply_theme` emits `DeprecationWarning`. | [README.md:289](file:///home/gfariello/VC/vistab/README.md), [README.md:313](file:///home/gfariello/VC/vistab/README.md); [docs/API.md:139-148](file:///home/gfariello/VC/vistab/docs/API.md); [src/vistab.py:1367-1370](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D4 | High | Low | SWE | Internal deprecated calls / docs-by-example (= DOC-01/05) | The CLI itself calls deprecated `apply_theme` ([src/vistab.py:3643](file:///home/gfariello/VC/vistab/src/vistab.py)), and `--show-code` **generates** code calling `apply_theme` ([src/vistab.py:3757](file:///home/gfariello/VC/vistab/src/vistab.py)) — actively teaching the deprecated call. Emits `DeprecationWarning` that pollutes test/CLI runs; the `regression_cli_show_code.txt` fixture encodes it. | [src/vistab.py:3643](file:///home/gfariello/VC/vistab/src/vistab.py), [src/vistab.py:3757](file:///home/gfariello/VC/vistab/src/vistab.py); [tests/fixtures/regression_cli_show_code.txt:27](file:///home/gfariello/VC/vistab/tests/fixtures/regression_cli_show_code.txt) |
| D5 | Medium | Low | Maintainer | Stale roadmap (= DOC-04) | `TODO.md:25` lists Colspan as a future `v1.2.0` roadmap item, though colspan is implemented, tested, and in CHANGELOG `[Unreleased]`. | [TODO.md:22-27](file:///home/gfariello/VC/vistab/TODO.md); [CHANGELOG.md:20](file:///home/gfariello/VC/vistab/CHANGELOG.md) |
| D6 | Low | Low | Novice | Version mismatch (= DOC-06) | `docs/API.md:3` titles the reference "v1.1.2"; the package is `1.1.3`. | [docs/API.md:3](file:///home/gfariello/VC/vistab/docs/API.md); [pyproject.toml:7](file:///home/gfariello/VC/vistab/pyproject.toml) |
| D7 | Low | Low | Novice / SWE | Docstring references deprecated method (= DOC-03) | The `__init__` docstring says it maps into `self.header()` (deprecated); it actually calls `self.set_header()`. | [src/vistab.py:781](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D8 | Low | Low | SWE | API reference completeness | `docs/API.md` §6 omits `set_theme`; the documented `__init__` signature (line 22) is outdated — the real constructor also accepts `title`, `max_rows`, `max_cols`, `theme` (verified via `inspect.signature`). Users cannot discover those from the doc. | [docs/API.md:22](file:///home/gfariello/VC/vistab/docs/API.md); actual sig in [src/vistab.py:781](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D9 | Low | Low | Novice | README prose clarity | High-traffic README passages are verbose/aspirational to the point of obscuring the action (e.g. Key Features bullets; "protect logging interfaces elegantly"). Not inaccurate; the documentation lens favors concise/clear. Cap to the highest-traffic sections; do not gold-plate. | [README.md:9-13](file:///home/gfariello/VC/vistab/README.md), [README.md:84-88](file:///home/gfariello/VC/vistab/README.md) |

## Proposed changes (ordered, validatable)

Fix by default; all Low Remediation Risk. Ordering: accuracy (D1-D7) first, then
completeness (D8), then optional polish (D9). Steps 3-5 use Gemini's fixture-safe sequence
(swap generator + internal call, sweep docs/examples, then regenerate the fixture in the
same pass) so `tests/test_regression.py` never goes red mid-sweep.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D1 | In `docs/CLI.md` "Diagnostic Endpoints", replace `-M`/`-L`/`-C` with `--demo themes`, `--demo styles`, `--demo colors` (and mention `capabilities`/`anatomy`); align with the README's `--demo` usage. | `docs/CLI.md` | Low | Every command shown in CLI.md runs without "unrecognized argument"; `python src/vistab.py --demo styles`/`themes`/`colors` succeed. |
| 2 | D2 | Fix `docs/CLI.md:44`: `--sort-by` takes a **column** index (0-indexed), not a row index. | `docs/CLI.md` | Low | Wording matches the CLI `--help` string and `sort_by` semantics. |
| 3 | D4 | In `src/vistab.py`, change the CLI's internal `apply_theme(args.theme)` call to `set_theme(...)`, and update the `--show-code` generator to emit `set_theme` instead of `apply_theme`. | `src/vistab.py` | Low | `python src/vistab.py <csv> --show-code` output uses `set_theme`; no `DeprecationWarning` from a normal CLI run. |
| 4 | D4 | Regenerate the gold-master fixture `tests/fixtures/regression_cli_show_code.txt` from the corrected generator (Step 3) so the regression test matches. Do this in the **same** change as Step 3. | `tests/fixtures/regression_cli_show_code.txt` | Low | `python -m pytest tests/test_regression.py` passes. |
| 5 | D3, D4 | Sweep remaining `apply_theme` -> `set_theme` in docs/examples/tests: README theming examples (lines 289, 313), `docs/API.md` §6 (document `set_theme`; keep one line noting `apply_theme` is a deprecated alias), `FUNCTIONAL_SPEC.md:29`, `examples/styled_matrix.py`, and the test call sites (`tests/test_regression.py`, `tests/test_config.py`). | `README.md`, `docs/API.md`, `FUNCTIONAL_SPEC.md`, `examples/styled_matrix.py`, `tests/test_regression.py`, `tests/test_config.py` | Low | `PYTHONPATH=. python -m pytest` passes **without** `-W ignore`; no `DeprecationWarning` in normal test/CLI runs. |
| 6 | D5 | Remove/relocate the Colspan "Target: v1.2.0" roadmap entry in `TODO.md`; note it as shipped (or delete). | `TODO.md` | Low | `TODO.md` no longer lists a shipped feature as future. |
| 7 | D6 | Update `docs/API.md` title version to match `pyproject.toml` (`1.1.3`) or make it version-agnostic to stop future drift (see Open Q3). | `docs/API.md` | Low | Version matches `pyproject.toml` (or no hardcoded version remains). |
| 8 | D7 | Fix the `__init__` docstring to reference `self.set_header()`. | `src/vistab.py` | Low | Docstring inspection. |
| 9 | D8 | In `docs/API.md`: correct the `__init__` signature to include `title`, `max_rows`, `max_cols`, `theme`; add `set_theme` to §6; point to `--demo styles` for the live list of style names. | `docs/API.md` | Low | Documented `__init__` signature matches `inspect.signature`; `set_theme` present; all documented method names resolve on `Vistab`. |
| 10 | D9 | Tighten the README Key Features and the two cookbook intros for clarity (concise, active). No new claims. | `README.md` | Low | Reviewer confirms no new/aspirational claims; length reduced, meaning preserved. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are Low Remediation Risk and proposed for action now. | - |

## Scope check

- **Over-scope:** none. D9 (prose polish) is capped to the highest-traffic sections to
  avoid rewrite bloat (Complexity axis).
- **Under-scope:** the deprecation-only framing of the first pass missed the dead CLI flags
  (D1) and the `--sort-by` axis error (D2) — the two highest-harm accuracy bugs for a CLI
  user. This merged plan includes them.

## Required tests / validation

- **Warnings-as-signal:** `PYTHONPATH=. python -m pytest` **without** `-W ignore` — no
  `DeprecationWarning` from normal execution after Steps 3-5.
- **CLI smoke:** run every command shown in `docs/CLI.md` and `README.md`
  (`--demo styles|themes|colors|capabilities|anatomy`, a `--show-code` run) and confirm none
  error.
- **Regression:** the `regression_cli_show_code` gold-master is regenerated in lockstep with
  Steps 3-4 so `tests/test_regression.py` stays green throughout.
- **Doc/code parity:** documented `__init__` signature matches `inspect.signature`; all
  method names in `docs/API.md` resolve on `Vistab`.
- **Visual check:** run `examples/styled_matrix.py` after the theme swap.

## Spec / documentation sync

This plan **is** the doc sync. `FUNCTIONAL_SPEC.md:29` currently names `apply_theme`; Step 5
updates it. If `apply_theme` disappears from all shipped code paths (only the deprecated
public method remains), add a one-line CHANGELOG `[Unreleased]` note (behavior-neutral but
user-visible in `--show-code`).

## Open questions

1. **Source IPDs:** this merged file supersedes `20260709-assess-documentation.md` and
   `20260709-assess-documentation-opencode.md`. Confirm both should be removed once this is
   approved (recommended).
2. **`--show-code` fixture:** confirm the gold-master should be **regenerated** from the
   corrected generator (Step 4) rather than hand-edited, to avoid drift.
3. **Version-in-docs policy (D6):** prefer a hard version string in `docs/API.md` (bumped
   each release) or a version-agnostic title? (Recommend version-agnostic.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute Steps 1-10 in order, run the validation, and sync docs/spec.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`
   per the project lifecycle. Plan files are named `YYYYMMDD-<slug>.md`.
