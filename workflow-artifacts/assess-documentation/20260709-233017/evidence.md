# Evidence - assess documentation (opencode run)

Reproducible from the files/commands below. No project files were changed.

## Docs read (full)
- `README.md` (397 lines) — features, quick start, cookbook, themes, limitations.
- `docs/API.md` (191 lines) — API reference.
- `docs/CLI.md` (95 lines) — CLI manual.
- `FUNCTIONAL_SPEC.md`, `CHANGELOG.md` (head), `TODO.md` (colspan section).
- The prior Gemini IPD `.agents/plans/pending/20260709-assess-documentation.md`.
- Workflow harness: `assess/lenses/documentation.md`, `assess/templates/*`,
  `release-review/fix-decision-policy.md`.

## Code / packaging verified against docs
- `pyproject.toml` — name/version (1.1.3), `[project.scripts] vistab = "vistab:main"`,
  optional `[cjk]`/`[dev]` extras, `wcwidth` dep.
- `src/vistab.py` — verified via `inspect` and runtime:
  - Styles `round-header/round/light/ascii/none` and themes
    `ocean/forest/graphite/orchid/sunflower/ocean-rows-index` all construct OK.
  - `apply_theme` present and emits `DeprecationWarning` (1367-1370); `set_theme` present.
  - `header()` deprecated (1836-1839); `__init__` docstring references `self.header()` (781).
  - CLI: `--demo` with choices styles/colors/capabilities/anatomy/themes (3332); `--sort-by`
    help says "Column index (0-indexed)" (3339); internal `apply_theme` call (3643);
    `--show-code` prints `apply_theme` (3757).
  - Real `__init__` signature includes `title, max_rows, max_cols, theme` (not in API.md).

## Commands run
- `date +%Y%m%d-%H%M%S` -> run ID 20260709-233017.
- `git status --short` (clean) and `git log --oneline` — confirmed colspan hardening executed
  (commits a3350b9, 1203449) and Gemini's doc IPD committed (bab26b5).
- Python one-liners: construct each documented style/theme; `inspect.signature` on
  `ColSpan.__init__`, `Vistab.__init__`, `stream`, `sort_by`; probe `colspan=0` (raises
  `ValueError`); reproduce overlap validation (raises `ValueError`).
- CLI probes: `python src/vistab.py --demo styles` (OK); `-M`/`-L`/`-C` (all absent/fail);
  `--stream-probe 5` (OK).
- `for f in examples/*.py: python $f` — all three run clean (basic_usage, colspan_demo,
  styled_matrix).
- `rg` for `apply_theme`/`set_theme`/`header(`/`sort-by`/`--demo` across src/docs/tests.

## Sampling / limits
- Did not exhaustively lint every prose sentence (D9 is scoped to high-traffic sections).
- Screenshots referenced in README/CLI were not fetched/verified (external asset URLs);
  not in scope for text-accuracy assessment.
