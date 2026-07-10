# Assessment run report - documentation

- Date / run ID: 20260709-233017
- Concern: documentation
- Scope: whole project docs, verified against `src/vistab.py` (v1.1.3) and packaging
- IPD written: `.agents/plans/pending/20260709-assess-documentation-opencode.md`
- Verdict: **needs work** for documentation — the docs are extensive and mostly accurate, but contain user-facing inaccuracies (dead CLI flags, a wrong sort axis, deprecated-API-as-primary) that a novice hits on first use.

Independent second pass. Confirms the prior Gemini IPD's findings and adds D1/D2/D8.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| D1 | High | Low | Novice/operator | `docs/CLI.md` documents `-M`/`-L`/`-C` diagnostic flags that no longer exist; CLI now uses `--demo {styles,colors,capabilities,anatomy,themes}`. |
| D2 | Medium | Low | Novice | `docs/CLI.md:44` calls `--sort-by` a "row index"; it is a **column** index (CLI help says so). |
| D3 | Medium | Low | Novice/SWE | README + `docs/API.md` present deprecated `apply_theme` as primary; `set_theme` undocumented. (= prior DOC-02) |
| D4 | Medium | Low | SWE | CLI calls `apply_theme` internally and `--show-code` generates `apply_theme` calls. (= prior DOC-01/05) |
| D5 | Medium | Low | Maintainer | `TODO.md` lists shipped Colspan as future v1.2.0. (= prior DOC-04) |
| D6 | Low | Low | Novice | `docs/API.md` titled v1.1.2; package is 1.1.3. (= prior DOC-06) |
| D7 | Low | Low | SWE | `__init__` docstring references deprecated `self.header()`. (= prior DOC-03) |
| D8 | Low | Low | SWE | `docs/API.md` `__init__` signature omits `title`/`max_rows`/`max_cols`/`theme`; `set_theme` missing from §6. |
| D9 | Low | Low | Novice | README prose is verbose/aspirational in high-traffic sections; tighten for clarity (no new claims). |

(Full list in `findings.csv`.)

## Proposed plan (summary)

1. CLI.md: replace dead `-M`/`-L`/`-C` with `--demo ...` (D1).
2. CLI.md: fix `--sort-by` to "column index" (D2).
3. Replace `apply_theme` -> `set_theme` in README, `--show-code` generator, CLI call, API §6, example, and the tests/fixture (D3/D4).
4. TODO.md: drop shipped-colspan roadmap entry (D5).
5. `docs/API.md` version -> 1.1.3 or version-agnostic (D6).
6. Fix `__init__` docstring to `set_header()` (D7).
7. Correct `__init__` signature + add `set_theme` in `docs/API.md` (D8).
8. Tighten README Key Features / cookbook intros (D9).

## Deferred (with reason)

- None. All findings Low Remediation Risk; proposed for action now.

## Out-of-repo / organizational notes (if any)

- None. All actions are in-repo doc/code/test edits.

## Next step

Review the IPD (optionally run `plan-review` and reconcile with the earlier
`20260709-assess-documentation.md`) and approve before execution. This workflow does not
execute the plan.
