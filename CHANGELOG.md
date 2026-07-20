[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-07-19

### Changed
- **Faster rendering** via internal micro-optimizations (byte-identical output): the per-cell
  data-type formatter map is built once instead of per cell, the span-boundary computation is
  skipped for tables with no column spans, and the RTL bidi scan is skipped when bidi is
  disabled. Measured ~17-29% faster on 1000-row scenarios. Added a `benchmarks/bench_render.py
  --summary` harness (informational; also runs non-gating in CI).

### Fixed
- **`draw()` now returns `""` instead of `None` for a truly empty table** (no header and no
  rows), matching its documented `-> str` contract. This makes `print(table.draw())` and
  `table.draw().splitlines()` safe for the empty case. A present-but-empty structure (for example
  `set_header([""])` or `add_row([""])`) still draws an empty one-cell box.
- **Integer columns now round half away from zero** (`2.5` -> `3`, `-2.5` -> `-3`) instead of
  Python's default banker's rounding (round-half-to-even, which gave `2.5` -> `2`). Affects the
  `i` and `I` data-type codes. This changes the rendered value only for exact `.5` inputs.
- **`None` in a numeric column now renders as an empty cell** instead of the literal string
  `"None"`. Affects the `a`/`i`/`I`/`f`/`F`/`e`/`E` codes; a text (`t`) column is unchanged.
- **A malformed `themes.json` no longer fails silently.** vistab now prints a warning (with the
  path and reason) to stderr and continues with the built-in themes, instead of swallowing the
  error.
- **Empty input no longer exits silently.** Piping empty data (or passing an empty file) now
  prints a short "no tabular data" guidance message to stderr and exits with code `1`, matching
  the documented exit semantics, instead of producing no output and exiting `0`.
- **Corrected the documented `Vistab(...)` constructor signature** in the API reference: the
  `header` parameter defaults to `None` and accepts `Union[bool, Iterable]`, not `bool = True`.
- Documented previously-undocumented public methods (`set_header_align`, `set_abnormal_row_style`)
  and the `vistab show showcase` CLI subject; surfaced right-to-left (`set_bidi`) support in the
  README; brought `FUNCTIONAL_SPEC` in line with the 1.2.x public API.

## [1.2.1] - 2026-07-17

### Added
- **Grouped-number column data types `F` and `E`.** `F` formats a float with thousands
  separators (e.g. `123,456.79`), mirroring how `I` relates to `i`; `E` is the grouped
  scientific form. Both accept the usual precision suffix (`F2`, `E4`) and fall back to text
  for non-numeric cells. Reachable from the CLI (`--dtype "F2"`). This closes the
  "commas AND decimals" gap without overloading the comma separator. Currency remains a
  documented callable (vistab does not guess a locale).
- **Documented number formatting** across `README`, `docs/API.md`, and `docs/CLI.md`,
  including the full column data-type code table, the precision suffix, and copy-paste
  callable recipes for grouped decimals and currency (`$`, other currencies, accounting
  negatives), noting vistab does not guess a locale.

### Changed
- **`set_cols_dtype` errors and CLI `--dtype` help now enumerate and explain every valid
  data-type code** (a/t/i/I/f/F/e/E) from a single source of truth, so an invalid code produces
  a self-documenting message instead of a bare list. The CLI format-error tip was also corrected
  (previously misleading and omitting `I`).

### Fixed
- **Import no longer fails on Python 3.9-3.13.** A return annotation used `typing.Set` without
  importing it. Python 3.14 defers annotation evaluation (PEP 649) so it imported there, but on
  3.9-3.13 the annotation was evaluated at definition time and raised
  `NameError: name 'Set' is not defined`, breaking every import of `vistab` (and the entire CI
  test matrix). `Set` is now imported.
- **CLI no longer crashes on non-UTF-8 terminals.** The CLI now forces `stdin`/`stdout`/`stderr`
  to UTF-8 at startup, so drawing tables with Unicode box-drawing characters and CJK/RTL content
  works under a POSIX `C`/`POSIX` locale (where stdout defaults to ASCII on Python < 3.14) and on
  Windows region codepages (e.g. cp1252). Previously these raised `UnicodeEncodeError` and printed
  a traceback instead of a table (this was also failing the GitHub Actions test matrix).

## [1.2.0] - 2026-07-11

### Added
- **Bidi-safe rendering of right-to-left text.** When a cell contains RTL script (Arabic,
  Hebrew, etc.), vistab now wraps each cell's content in Unicode LTR isolates
  (`U+2066`..`U+2069`) so the terminal no longer reorders the whole line and flips the
  columns; the RTL text still reads correctly inside its cell. Isolates are zero-width, so
  column geometry is unchanged and non-RTL tables are byte-identical. Toggle with the new
  chainable `set_bidi()` API (default on) or the `--no-bidi` CLI flag for terminals that
  ignore isolates.
- **`vistab show showcase`** (also `demo showcase` / `--demo showcase`): a curated one-table
  demonstration combining column spanning, a theme, CJK/Thai/Arabic/Hebrew content, ANSI, and
  color-aware word-wrapping, fitting within 80 columns. Honors `--no-color` and `--no-bidi`.
- **`--no-color` / `NO_COLOR`.** New CLI flag (and honored env var) that disables all of
  vistab's own color/style output table-wide; also exposed on the library as
  `Vistab.set_color(enabled=True)`. User-supplied ANSI in cell content is left untouched.
- **`vistab show span`** (previously only `demo span`); `spans` is accepted as an alias, and
  `show wrapping` aliases `show capabilities`.
- **Column Spanning (Colspan) support**: Added first-class column spanning for both headers and rows, enabling cells to merge across multiple adjacent columns.
- **`ColSpan` wrapping data model**: Introduced `ColSpan` wrapper to declare spans inline during ingestion, supporting both `colspan` and `span` keyword arguments.
- **`set_header_span` and `set_cell_span` mutators**: Programmatic APIs to dynamically configure column spans post-ingestion. Supports negative indices.
- **Transactional Grid Validation**: Integrated comprehensive overlap, placeholder targeting, and non-empty overwrite checks to prevent silent grid corruption and KeyErrors during draws.
- **Line suppression & layout routing**: Automatically calculates column widths across spans, wraps text to merged block boundaries, and suppresses interior horizontal intersections/junctions underneath spanned cells.
- **`NOTICE`** file with the required Apache-2.0 attribution string; **`CITATION.cff`** added for
  citation; README gained a License/Attribution/Citation section.
- **Subject/Verb/Object CLI Subcommands**: Added natural-language subcommand structure (`show`, `help`, `demo`) as the primary CLI entry points, supporting aliases like `show caps`, `help adv`, and `demo span` (prints colspan demo alongside its Python code). Existing flags remain supported as aliases.

### Changed
- **License changed from BSD-3-Clause to Apache-2.0.** Now licensed under the Apache License 2.0
  (see `LICENSE` and the new `NOTICE`). Apache-2.0 requires redistributions and derivative works to
  retain the `NOTICE` file and display its attribution reasonably prominently ("Based on the original
  vistab by Gabriele G. R. Fariello, https://github.com/fariello/vistab"), and adds an explicit
  patent grant. Copyright holder normalized to the full legal name **Gabriele G. R. Fariello**.
- **Theme API Standardization**: Promoted `set_theme()` as the official API; `apply_theme()` is deprecated (emits `DeprecationWarning`).
- **Internal Cell Representation**: Row/header entries are now wrapped in `VistabCell` objects internally. While public API usage is unaffected, code that accesses the private `_rows` or `_header` structures directly must now use `str(cell)` to extract string values.
- **`set_header_span` and `set_cell_span` mutators**: Added a `combine` string parameter (default `" "`) to merge existing covered cell values together, with `combine=None` triggering strict overwrite-prevention validation.
- **Span demo (`show span`) redesigned:** example code is printed directly beneath the table it produced, with the span-specific calls highlighted; color-focused demos print a `WARNING: colors turned off ...` notice when color is suppressed.
- **Library-first framing:** the module docstring, `README.md`, `AGENTS.md`, and the CLI usage/no-data output now foreground `from vistab import Vistab` as the primary interface, positioning the CLI as a secondary, ad-hoc surface. No API, CLI, or rendering behavior changed.

### Fixed
- **Colspan now honors `max_width`.** A spanned (colspan) cell whose merged content exceeded
  its combined column budget used to widen the covered columns past `max_width`, blowing the
  documented hard width ceiling. It now expands to fit only as far as the remaining budget
  allows and wraps the rest within its block, like any other cell. Spans without a ceiling
  still expand to fit on one line as before.
- Repaired a broken screenshot link in `docs/CLI.md` (referenced a non-existent
  `vistab-M-themes-output.png`, a leftover of the removed `-M` flag).
- **`has_header = False` now un-headers row 0.** Previously, a table built via `Vistab(rows)` (no explicit `header=`) consumed row 0 as a header, and setting `has_header = False` afterward suppressed the divider but still rendered row 0 with centered header alignment. The setter now moves the consumed row back into the data rows (span-safe) and cell alignment is gated on `has_header`, so that row uses the body `alignment=`. Setting `has_header = True` re-consumes the current first row.



## [1.1.3] - 2026-05-03

### Added
- **`theme` constructor parameter**: `Vistab()` now accepts `theme` as a keyword argument (string or dict), applied after all other settings so it can cleanly override `style`, `padding`, etc. set at construction time.
- **`set_theme()` method**: `apply_theme()` has been renamed to `set_theme()` to match the `set_*` convention used by every other method in the class.

### Deprecated
- **`apply_theme()`**: The old name still works but emits a `DeprecationWarning`. It will be removed in a future minor release.

## [1.1.2] - 2026-04-13

### Fixed
- Changed relative image links in `README.md` to absolute URLs to prevent broken images on PyPI.
- Pinned `setuptools` build dependency to `<69.0` in `pyproject.toml` to resolve metadata parsing errors during PyPI upload.

## [1.1.0] - 2026-04-10

### Added
- **Diagnostic Demo Tests**: Added `tests/test_demo.py` dedicated to tracking regression matrices for the `--demo` configurations (`styles`, `colors`, `capabilities`, `anatomy`, `themes`).
- **Dynamic Auto-Dtype Inference**: The `a` (automatic) datatype now scans column bounds before format ingestion, upgrading columns structurally to uniform floats (`f`) or scientific notation (`e`).
- **Inline Custom Precisions**: You can now attach custom precision overrides inside dtype string arrays (e.g. `set_cols_dtype(["i", "f2", "e4", "a"])` or via CLI `--dtype "if2e4a"`).
- **Single-String List Unpacking API**: Standard array methods like `set_cols_align` now accept unboxed single-element strings (e.g., passing `["clrcr"]` unpacks to `["c", "l", "r", "c", "r"]`).
- **CLI Structural Override**: Added the `--style-def` CLI argument supporting 15-character string boundary declarations to override built-in layout constants.
- **Mathematical Word Chunking**: Chunks contiguous strings to map colors while spanning ANSI bounds.
- **ANSI Layout Reassertion / Masking**: Exposed `sanitize_ansi` to purge destructive positional cursor controls. Reasserts nested text styles bridging wrapped cell boundaries.
- **Infinite Generator Streaming**: Introduced `Vistab.stream()` providing memoryless arrays for infinite streams. Added `--stream` and `--stream-probe`.
- **Jagged Matrix Resolution**: Added `--on-short=pad` and `--on-long=truncate` to fix irregular CSVs. Included dynamic cell highlighting (`--mark-abnormal COLOR`).
- **Dynamic Array Routing System**: Added `--sort-by` and `--sort-reverse` inherently sorting pipeline structures locally.
- **Dialect Pipeline Controls**: Added `--csv-dialect` directing CSV pipeline resolution.
- **Global Theme Washes**: Implemented `table.set_table_style()` and `--table-bg-color` (`-g`) flag to apply universal foregrounds or backgrounds.
- **Negative Coordinate Architecture**: Re-engineered rendering logic to accept `-1` indexing. Added `--last-col-color` (`-x`), `--last-col-bg-color` (`-y`), `--last-row-color` (`-l`), and `--last-row-bg-color` (`-A`).
- **CLI Configuration Workflows**: Added native `--save-theme` workflow generating `~/.config/vistab/themes.json` allowing user-defined themes to persist.
- **Python Initialization Expansion**: Enhanced `--show-code` to output method bindings for data parameters (like `--align` or `--width`), decoupling them from base layouts.

### Fixed
- **Documentation Overhaul**: Conducted a complete formal overhaul of `FUNCTIONAL_SPEC.md`, `README.md`, `docs/API.md`, and `docs/CLI.md` removing redundant phrasing and injecting explicit "Limitations & Known Gaps". 
- **State Corruption on Generator Intersections**: Addressed internal generator pipelines to prevent purging primary table geometries on stream intersections.
- **ANSI Terminal Compatibility**: Decoupled chained ANSI escape sequences into distinct isolated tokens resolving attribute clipping in Windows and WSL terminals.
- **Cell Vertical Alignment Crashes**: Fixed `unhashable type: list` crash during boundary sizing logic by migrating away from `_vislen` bounds.
- **CLI Parser Mappings**: Resolved an internal mapping conflict renaming the visual `--row0-color` parameter properly assigning it directly to `--col0-color` (`-0`).

## [1.0.3] - 2026-04-06

### Documentation
- **General Cleanup**: Refactored the core documentation suite (`README.md`, `CHANGELOG.md`, `docs/API.md`, `docs/CLI.md`, `TODO.md`) to use concise, professional language and structure.
- **Web Rendering**: Replaced the text-based example output in the `README.md` with an image screenshot. This resolves an issue where PyPI's limited font stack (e.g., `Source Code Pro`) failed to render specific Unicode Box Drawing characters with accurate monospace widths.
- **Changelog**: Added `CHANGELOG.md` to formally track standard semantic version releases.

## [1.0.2] - 2026-04-06

### Fixed
- **CLI**: The `--padding 0` configuration logic is no longer overridden when applying themes to a table output.
- **CLI**: The STDIN parser (`csv.Sniffer`) now restricts delimiter discovery rules to standard characters (`,\t|;`). This prevents `vistab` from splitting individual English words when piping simple strings to the CLI (e.g., `echo "Speed" | vistab`).
- **Core Rendering Engine**: Title width evaluation logic now correctly respects the internal array padding configurations, allowing headers to center properly across column bounds.

## [1.0.1] - 2026-04-05

### Added
- **Multi-File Executions**: The CLI now supports processing multiple sequential files (e.g., `vistab data1.csv data2.csv logs.tsv`), iterating through them without requiring the legacy `-i` flag.
- **STDIN Core Rendering Architectures**: The CLI can now capture UNIX pipes, allowing raw command executions to be passed in (e.g., `cat mydata.csv | vistab --theme ocean`).

### Fixed
- **Geometry Overflow Boundaries**: Improved the core sequence mapping for truncation fallbacks. Unbroken strings that exceed wrap limits now trigger a visual truncation fallback instead of raising an error.
- **Single-Row Header Overlap**: Modified `add_rows()` and `draw()` to correctly evaluate single-row tables (header only), preventing the middle separator line from overlapping with the bottom border.

## [1.0.0] - 2026-04-05

*Major update migrating the original local `unitable.py` script into the standalone `vistab` Python utility library.*

### Added
- **Fluent Object-Oriented Framework**: The `Vistab` instance supports method chaining to modify states quickly (e.g., `table.set_title("X").set_padding(2).set_max_rows(5).draw()`).
- **Unified Configuration Engines (TOML)**: The library supports localized `.vistab.toml` or `~/.config/vistab.toml` configuration files.
- **Command-Line Interface (CLI)**: Developed a standalone CLI to format tables via flags (`--width`, `--padding`, `--max-rows`, `--align`, `--theme`, etc.).
- **Dynamic Thematic Striping Matrices**: Configured 18 pre-built layout themes with Zebra-Striping colors (e.g., `ocean-index`, `forest-cols`, `minimalist-solid`).
- **Comprehensive ANSI Mapping Frameworks**: The internal width calculator bypasses ANSI configuration sequences, ensuring borders align correctly when colors are applied.
- **Diagnostic Execution Modes**: Added diagnostic terminal options (`-M` for Themes, `-L` for Styles, `-C` for Terminal Color Support, `-T` for the ANSI bypass test suite).

---
[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
