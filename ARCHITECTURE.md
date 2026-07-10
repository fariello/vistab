[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Vistab Architecture

A short cold-start orientation for engineers and LLMs. For exhaustive behavior, see
[FUNCTIONAL_SPEC.md](FUNCTIONAL_SPEC.md); for the *why* behind major decisions, see the
executed plans under `.agents/plans/executed/` and [CHANGELOG.md](CHANGELOG.md).

## What it is

`vistab` is a lightweight, dependency-minimal (only `wcwidth`) pure-Python library **and**
CLI for rendering ANSI-aware, CJK-width-correct Unicode/ASCII terminal tables. Design
values (observed, not from a separate principles file): intuitive/self-documenting,
general-case/configurable over hardcoded, KISS, and honest documentation.

## Shape of the codebase

Everything lives in **one module, `src/vistab.py`** (packaged as a top-level `py-module`,
console entry point `vistab = "vistab:main"`). This is a deliberate single-file design for
a small, focused tool; a module split is a possible future refactor but is not required
(recorded in the release-review as deferred, low value / higher churn risk).

Key classes/functions:

- **`Vistab`** — the table object and fluent public API: ingestion (`set_header`,
  `add_row(s)`, `set_rows`), styling (`set_*_style`, `set_theme`; `apply_theme` is a
  deprecated alias), spanning (`ColSpan`, `set_cell_span`, `set_header_span`), layout
  (`set_cols_align/valign/dtype`, `set_max_*`, `set_padding`), and output (`draw`,
  `stream`).
- **`ColSpan` / `VistabCell` / `VistabPlaceholderCell`** — the cell data model. Cells are
  objects (string-transparent via `__str__`); a spanned "source" cell is followed by
  `colspan-1` placeholder cells so the grid stays physically rectangular.
- **`StringLengthCalculator`** — visible-width measurement that ignores ANSI escapes
  (LRU-cached); **`ColorAwareWrapper`** — word wrapping that preserves ANSI sequences.
- **`main()`** — the CLI: natural-language subcommands (`show`/`help`/`demo`) dispatched
  before argparse, with the classic flags retained as aliases.

## The render pipeline

The core flow is a linear pass (see `draw()` / `stream()`):

1. **Ingest** rows/header into `VistabCell` objects; `ColSpan` expands to source +
   placeholders; jagged rows handled by `on_short_row`/`on_long_row` policies.
2. **Compute column widths** (`_compute_cols_width`) — natural widths, then distribute a
   spanned cell's deficit across its covered columns.
3. **Wrap** cell text to (possibly merged) column widths (`_splitit`, ANSI-safe).
4. **Draw** each line (`_draw_line`) and the horizontal rules (`_build_hline`), which
   render directional box-junctions (`┬`/`┴`/`┼`/`─`) correctly around spanned blocks.

`stream()` is memory-bounded: it samples the first N rows to fix geometry, then yields
rows without buffering. Sorting a stream (`--sort-by`) is explicitly rejected because it
would require buffering the whole input.

## Security & safety surface

Minimal by design: no auth, network, secrets, `eval`/`exec`, or subprocess. The one
security-relevant feature is `sanitize_ansi`, which strips destructive cursor-movement
escape sequences to prevent terminal-display hijacking.

## Where to go next

- Behavior contract & edge cases: `FUNCTIONAL_SPEC.md`
- Public API / CLI: `docs/API.md`, `docs/CLI.md`
- Decision rationale (colspan, combine, has_header, CLI verbs, etc.): `.agents/plans/executed/`
