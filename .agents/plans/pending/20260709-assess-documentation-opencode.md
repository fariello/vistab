# IPD: Assess documentation - accuracy sweep across README, API, CLI, SPEC, TODO

- Date: 2026-07-09
- Concern: documentation
- Scope: whole project docs — `README.md`, `docs/API.md`, `docs/CLI.md`, `FUNCTIONAL_SPEC.md`, `TODO.md`, `CHANGELOG.md`, inline docstrings. Verified against `src/vistab.py` (v1.1.3) and packaging.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Relationship to the existing documentation IPD.** A prior `assess documentation` run
> (Antigravity/Gemini) produced `.agents/plans/pending/20260709-assess-documentation.md`,
> focused on deprecated-method references (`apply_theme`/`header`), a stale `TODO.md`
> colspan item, and the `docs/API.md` version number. This IPD is an **independent,
> deeper** pass under the documentation lens. It **confirms** those findings (re-verified
> against code) and **adds** several the earlier pass missed — most importantly
> **`docs/CLI.md` documents CLI flags that no longer exist** (`-M`/`-L`/`-C`), and a
> `--sort-by` semantics error. Overlapping findings are cross-referenced (the earlier
> IPD's DOC-IDs are cited). Recommend executing this superset and retiring/merging the
> earlier IPD, or running `plan-review` to reconcile the two.

## Goal

Make every user-facing doc describe what `vistab` actually does **today**, so a novice
following the README/CLI docs reaches a first success without hitting a command or method
that errors, and a maintainer can trust the API reference. Documentation lens priority:
**fix inaccuracies first** (highest harm), then fill small gaps; keep it concise (no bloat).

## Project conventions discovered (Step 0)

- **Intent / audience / stack:** `vistab` is a lightweight pure-Python terminal-table
  library **and** CLI (`src/vistab.py`, v1.1.3 per `pyproject.toml`), published to PyPI
  (`pip install vistab`, console script `vistab = "vistab:main"`, optional `[cjk]` extra).
  Audience: Python developers and CLI users. Docs are the primary onboarding surface.
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`; universal fallback applies —
  **honest docs over impressive docs**, intuitive/self-documenting, KISS.
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **Contributor/spec-sync contract:** `AGENTS.md` (workflow index only). `CHANGELOG.md`
  follows Keep-a-Changelog; colspan is correctly under `[Unreleased]`.
- **Scope exclusions:** `.agents/workflows/` and `workflow-artifacts/` are not assessed as
  project docs.
- **Positive baseline (verified, do not "fix"):** README styles (`round-header`, `round`,
  `light`, `ascii`, `none`) and themes (`ocean`, `forest`, `graphite`, `orchid`,
  `sunflower`, `ocean-rows-index`) all exist; all `docs/API.md`-listed methods exist; all
  three `examples/*.py` run clean; the colspan usability hardening (`ColSpan(colspan=/span=)`,
  overlap/placeholder validation, `IndexError`/`ValueError`, `colspan=1` no-op) **has been
  implemented**, so the `docs/API.md` colspan section (lines 53-60) is now accurate.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate. Persona = surfacing view.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D1 | High | Low | Novice / operator | CLI docs accuracy (dead flags) | `docs/CLI.md` documents diagnostic flags `-M`, `-L`, `-C` (lines 74-76), but these **no longer exist**; the CLI now uses `--demo {styles,colors,capabilities,anatomy,themes}` (which the README already uses). A novice following CLI.md's diagnostics gets an error. | [docs/CLI.md:74-76](file:///home/gfariello/VC/vistab/docs/CLI.md); flag def [src/vistab.py:3332](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D2 | Medium | Low | Novice | CLI docs accuracy (wrong semantics) | `docs/CLI.md:44` describes `--sort-by INDEX` as "a specified **row** index," but it is a **column** index (the CLI help string itself says "Column index (0-indexed)"). Misleads users into sorting by the wrong axis. | [docs/CLI.md:44](file:///home/gfariello/VC/vistab/docs/CLI.md); [src/vistab.py:3339](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D3 | Medium | Low | Novice / SWE | Docs advertise deprecated API | README (Custom Themes) and `docs/API.md` §6 present `apply_theme` as the primary theming method; `set_theme` (the non-deprecated replacement) is undocumented. `apply_theme` emits `DeprecationWarning`. (Confirms earlier IPD DOC-02.) | [README.md:289](file:///home/gfariello/VC/vistab/README.md), [README.md:313](file:///home/gfariello/VC/vistab/README.md); [docs/API.md:139-148](file:///home/gfariello/VC/vistab/docs/API.md); [src/vistab.py:1367-1370](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D4 | Medium | Low | SWE | Internal deprecated calls (doc-by-example) | The CLI itself calls the deprecated `apply_theme` ([src/vistab.py:3643](file:///home/gfariello/VC/vistab/src/vistab.py)), and `--show-code` **generates** code that calls `apply_theme` ([src/vistab.py:3757](file:///home/gfariello/VC/vistab/src/vistab.py)), teaching users the deprecated call. The `regression_cli_show_code.txt` fixture encodes it. (Confirms earlier IPD DOC-01/DOC-05.) | [src/vistab.py:3643](file:///home/gfariello/VC/vistab/src/vistab.py), [src/vistab.py:3757](file:///home/gfariello/VC/vistab/src/vistab.py); [tests/fixtures/regression_cli_show_code.txt:27](file:///home/gfariello/VC/vistab/tests/fixtures/regression_cli_show_code.txt) |
| D5 | Medium | Low | Maintainer | Stale roadmap | `TODO.md:25` lists Colspan as a future `v1.2.0` roadmap item, but colspan is implemented, tested, and in the CHANGELOG `[Unreleased]`. (Confirms earlier IPD DOC-04.) | [TODO.md:22-27](file:///home/gfariello/VC/vistab/TODO.md); [CHANGELOG.md:20](file:///home/gfariello/VC/vistab/CHANGELOG.md) |
| D6 | Low | Low | Novice | Version mismatch | `docs/API.md:3` titles the reference "v1.1.2"; the package is `1.1.3`. (Confirms earlier IPD DOC-06.) | [docs/API.md:3](file:///home/gfariello/VC/vistab/docs/API.md); [pyproject.toml:7](file:///home/gfariello/VC/vistab/pyproject.toml) |
| D7 | Low | Low | Novice / SWE | Docstring references deprecated method | The `__init__` docstring says it maps into `self.header()` (deprecated); it actually calls `self.set_header()`. (Confirms earlier IPD DOC-03.) | [src/vistab.py:781](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D8 | Low | Low | SWE | API reference completeness | `docs/API.md` §6 omits `set_theme` and does not mention `set_style`'s valid style names beyond examples; the `__init__` doc (line 22) lists an outdated signature — the real constructor also accepts `title`, `max_rows`, `max_cols`, `theme` (verified via `inspect.signature`). Users cannot discover those from the doc. | [docs/API.md:22](file:///home/gfariello/VC/vistab/docs/API.md); actual sig in [src/vistab.py](file:///home/gfariello/VC/vistab/src/vistab.py) |
| D9 | Low | Low | Novice | README prose clarity (self-doc cross-ref) | Several README passages are verbose/aspirational to the point of obscuring the action (e.g. "Injects automatic text wrapping, infers scientific datatypes"; "protect logging interfaces elegantly"). Not inaccurate, but the documentation lens favors concise/clear. Tighten the highest-traffic sections (Key Features, Quick Start intro). Low priority; do not gold-plate. | [README.md:9-13](file:///home/gfariello/VC/vistab/README.md), [README.md:84-88](file:///home/gfariello/VC/vistab/README.md) |

## Proposed changes (ordered, validatable)

Fix by default; all Low Remediation Risk. Accuracy fixes (D1-D7) first, then completeness
(D8), then optional polish (D9). Steps overlap the earlier IPD where noted — execute once.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D1 | In `docs/CLI.md` "Diagnostic Endpoints", replace `-M`/`-L`/`-C` with `--demo themes`, `--demo styles`, `--demo colors` (and mention `capabilities`/`anatomy`). Match the README's `--demo` usage. | `docs/CLI.md` | Low | Every command shown in CLI.md runs without "unrecognized argument"; `python src/vistab.py --demo styles` etc. succeed. |
| 2 | D2 | Fix `docs/CLI.md:44`: `--sort-by` takes a **column** index (0-indexed), not a row index. | `docs/CLI.md` | Low | Wording matches the CLI `--help` string and `sort_by` semantics. |
| 3 | D3, D4 (== earlier DOC-01/02/05) | Replace `apply_theme` with `set_theme` in: README theming examples + generated `--show-code` output (`src/vistab.py:3757`), the CLI's own call (`src/vistab.py:3643`), `docs/API.md` §6 (document `set_theme`; keep a one-line "`apply_theme` is a deprecated alias"), `examples/styled_matrix.py`, and the tests/fixtures that assert the generated code. | `README.md`, `docs/API.md`, `src/vistab.py`, `examples/styled_matrix.py`, `tests/test_regression.py`, `tests/test_config.py`, `tests/fixtures/regression_cli_show_code.txt` | Low | `python -m pytest` passes **without** `-W ignore`; no `DeprecationWarning` in normal CLI/test runs; `--show-code` output uses `set_theme`. |
| 4 | D5 (== DOC-04) | Remove/relocate the Colspan "Target: v1.2.0" roadmap entry in `TODO.md`; note it as shipped (or delete). | `TODO.md` | Low | `TODO.md` no longer lists a shipped feature as future. |
| 5 | D6 (== DOC-06) | Update `docs/API.md` title version to match `pyproject.toml` (`1.1.3`), or make it version-agnostic to avoid future drift. | `docs/API.md` | Low | Version matches `pyproject.toml`. |
| 6 | D7 (== DOC-03) | Fix the `__init__` docstring to reference `self.set_header()`. | `src/vistab.py` | Low | Docstring inspection. |
| 7 | D8 | In `docs/API.md`: correct the `__init__` signature to include `title`, `max_rows`, `max_cols`, `theme`; add `set_theme` to §6; note where the current list of style names can be seen (`--demo styles`). | `docs/API.md` | Low | Documented `__init__` signature matches `inspect.signature`; `set_theme` present. |
| 8 | D9 | Tighten the README Key Features and the two cookbook intros for clarity/accuracy (concise, active). No new claims. | `README.md` | Low | Reviewer confirms no new/aspirational claims; length reduced, meaning preserved. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are Low Remediation Risk and proposed for action now. | - |

## Scope check

- **Over-scope:** none. D9 (prose polish) is capped to the highest-traffic sections to
  avoid rewrite bloat (Complexity axis).
- **Under-scope (vs. the earlier IPD):** the earlier documentation IPD missed the dead CLI
  flags (D1) and the `--sort-by` axis error (D2) — the two highest-harm accuracy bugs for a
  CLI user. This IPD adds them.

## Required tests / validation

- **Warnings-as-signal:** `PYTHONPATH=. python -m pytest` **without** `-W ignore` — no
  `DeprecationWarning` from normal execution after Step 3.
- **CLI smoke:** run each command shown in `docs/CLI.md` and `README.md` (`--demo styles`,
  `--demo themes`, `--demo colors`, `--demo capabilities`, a `--show-code` run) and confirm
  none error.
- **Regression:** the `regression_cli_show_code` gold-master fixture is updated in lockstep
  with Step 3 so `tests/test_regression.py` stays green.
- **Doc/code parity:** the documented `__init__` signature matches `inspect.signature`; all
  method names in `docs/API.md` resolve on `Vistab`.

## Spec / documentation sync

This plan **is** the doc sync. Additionally: add a short CHANGELOG note if `apply_theme`
usages are removed from shipped code paths (behavior-neutral but user-visible in
`--show-code`). `FUNCTIONAL_SPEC.md` already references themes correctly; verify no
`apply_theme` there during Step 3.

## Open questions

1. **Reconcile with the earlier IPD:** merge this superset into
   `20260709-assess-documentation.md`, or execute this one and retire that? (Recommend:
   execute this superset; it contains all of the earlier findings plus D1/D2/D8.)
2. **`--show-code` regeneration:** confirm the gold-master fixture should be regenerated
   from the corrected generator (Step 3) rather than hand-edited, to avoid drift.
3. **Version-in-docs policy (D6/D5):** prefer a hard version string in `docs/API.md` (must
   be bumped each release) or a version-agnostic title? (Recommend version-agnostic to stop
   recurring drift.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it and reconcile with the
   earlier documentation IPD).
2. On approval, execute Steps 1-8 in order, run the validation, and sync docs/spec.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`
   per the project lifecycle. Plan files are named `YYYYMMDD-<slug>.md`.
