# 01 Repository Inventory

## Project state summary
`vistab` — a lightweight pure-Python library + CLI for rendering ANSI-aware Unicode/ASCII
terminal tables. Mature and actively developed; 15 commits ahead of `origin/main` (all
this session's work: colspan feature, hardening, CLI subcommands, has_header fix, docs).

## Project type & scope
- Single source module `src/vistab.py` (4059 lines). Library API (`Vistab`, `ColSpan`,
  `StringLengthCalculator`, `ColorAwareWrapper`, `ArraySizeError`) + `main()` CLI.
- Packaging: `pyproject.toml` (setuptools), `py-modules=["vistab"]`, console script
  `vistab = "vistab:main"`, dep `wcwidth`, optional `[cjk]` (`cjkwrap`), `[dev]` (`pytest`).
  `requires-python >= 3.7`.

## Intended outcome / audience
Render beautiful, correctly-aligned terminal tables with color-aware wrapping (ANSI +
CJK width safety). Audience: Python developers (library API) and CLI users (CSV/TSV
rendering, theming). Stakeholder goal: a lightweight, dependency-minimal, self-documenting
alternative to heavier table libs.

## Guiding-principles document
None present (`GUIDING_PRINCIPLES.md`/`PRINCIPLES.md` absent). **Universal fallback
principles apply** (intuitive/self-documenting, general-case/configurable, KISS, honest
docs) — recorded per `00-run-protocol.md`.

## Backlog / TODO sources
- `TODO.md` — current and honest: colspan marked "Completed in v1.2.0"; rowspan and
  auto-align-plain-rows deferred with rationale; 3 CLI usability ideas (`--delimiter`,
  `--auto-width`, `--json-out`) as future considerations. **Verified none of the 3 are
  release blockers** (genuinely future).
- In-code `TODO`/`FIXME`/`HACK`/`XXX`: **none** in `src/vistab.py`.

## Pending agent plans / staged prompts
- `.agents/plans/pending/` — **empty** (only `.gitkeep`).
- `.agents/prompts/pending/` — **empty**.
- `.agents/plans/executed/` holds 10 completed IPDs (colspan suite, perf, docs, CLI verbs,
  has_header). `.agents/prompts/executed/` holds the has_header bug prompt.
- **No pending/unexecuted work and no status/location mismatches** → no Section 8 blocker
  from this axis.

## Public contract summary
- Library: `Vistab` fluent API (`set_header`, `add_row(s)`, `set_rows`, `draw`, `stream`,
  `sort_by`, styling `set_*_style`, `set_theme`/deprecated `apply_theme`, span mutators
  `set_cell_span`/`set_header_span`, `ColSpan`). `has_header` property.
- CLI: `vistab [flags] [files]` + verb subcommands (`show`/`help`/`demo`); flags retained
  as aliases. `--version` reports `vistab 1.1.3`.

## Test & validation inventory
7 test files, **101 tests passing** at run start: `test_vistab.py` (core + colspan +
has_header), `test_cli.py` (verb subcommands), `test_config.py`, `test_demo.py`
(fixture-based demo output), `test_edge.py`, `test_regression.py` (gold-master fixtures),
`test_streaming.py`. Validation command: `python -m pytest`.

## Documentation inventory
`README.md`, `docs/API.md`, `docs/CLI.md`, `FUNCTIONAL_SPEC.md`, `CHANGELOG.md` (Keep-a-
Changelog), `TODO.md`, `LICENSE` (Apache-2.0), `NOTICE`, `CITATION.cff`. No
`ARCHITECTURE.md`/`DECISIONS.md` (KD candidate — but `FUNCTIONAL_SPEC.md` covers much
architecture, and `.agents/plans/executed/` holds decision rationale).

## Build / packaging / CI / release
- `pyproject.toml` present and valid; `.github/` present. CI assessment deferred to §6.
- Version: `1.1.3` in both `pyproject.toml` and `__version__`.

## Drift / inconsistencies (with IDs)
- **20260710-194844-S1-BUG1 (version/release-state drift):** `pyproject.toml`/`__version__`
  say `1.1.3`, but `CHANGELOG.md [Unreleased]` and `TODO.md` ("Colspan Completed in v1.2.0")
  describe a v1.2.0's worth of shipped-but-unreleased work. Version has not been bumped for
  the unreleased feature set. Release-readiness concern. Evidence: pyproject.toml:7,
  vistab.py:93, CHANGELOG.md:10, TODO.md §2.
- **20260710-194844-S1-Q1 (LSP/type-hint noise):** the editor LSP reports ~100+ type
  errors in `src/vistab.py` (e.g. `draw() -> Optional[str]` used in `assertIn`, wcwidth
  param-name mismatch, `Optional` bool defaults). Runtime-harmless (all 101 tests pass) but
  worth noting for maintainability. To assess in §2.

## Recent changes
15 unpushed commits this session: colspan support + usability hardening + behavior
decisions + junction-glyph remediation; performance/documentation assessments; CLI
subject/verb/object subcommands; theme-demo tweaks; `has_header=False` alignment fix.

## Out-of-scope (per 00-run-protocol)
`.agents/workflows/` (this framework) and `workflow-artifacts/` (run records) are present
but NOT reviewed as project code.

## Recommended next actions
- §6: decide version bump (F1) as a release prerequisite.
- §2: assess the type-hint situation (Q1); hunt MEM/LIVE on the render/stream paths.
