[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-10

### Added
- **Dynamic Auto-Dtype Inference**: The `a` (automatic) datatype now safely scans column bounds recursively before format ingestion, seamlessly upgrading entire columns structurally to uniform floats (`f`) or scientific notation (`e`) cleanly.
- **Inline Custom Precisions**: You can now attach custom precision overrides dynamically specifically inside the dtype string arrays locally (e.g. `set_cols_dtype(["i", "f2", "e4", "a"])` or via CLI `--dtype "if2e4a"`).
- **Single-String List Unpacking API**: Standard array API methods like `set_cols_align` now accept dynamically unboxed single-element strings (e.g., passing `["clrcr"]` unpacks cleanly back to `["c", "l", "r", "c", "r"]`).
- **CLI Structural Override**: Added the `--style-def` CLI argument natively supporting 15-character string boundary declarations overriding built-in layout constants.
- **Mathematical Word Chunking**: Dynamically chunks contiguous strings to cleanly map executing color contexts while spanning ANSI bounds securely natively.
- **ANSI Layout Reassertion / Masking**: Exposed `sanitize_ansi` property on the `Vistab` class gracefully purging destructive positional cursor control sequences, alongside intelligent context reassertion mapping nested text styles spanning wrapped grid cell boundaries dynamically.
- **Infinite Generator Streaming**: Introduced `Vistab.stream()` providing natively memoryless mapping bounds for infinite streams, integrating pipe streams without full memory allocations. Added `--stream` and `--stream-probe`.
- **True Caveat Emptor Boundary Routing**: Explicitly evaluated the core engine implicitly handling memory constraints on OS efficiently. Combining `--stream` with highly constrained pipeline structural mappings natively triggers safe fallback to array buffering iteratively.
- **Jagged Matrix Resolution**: Added structural boundaries padding (`--on-short=pad`) and truncating (`--on-long=truncate`) irregular CSV row formats efficiently. Included dynamic cell highlighting (`--mark-abnormal COLOR`) to point out pipeline flaws visually.
- **Dynamic Array Routing System**: Added `--sort-by` and `--sort-reverse` inherently sorting pipeline structures locally accurately.
- **Dialect Pipeline Controls**: Added `--csv-dialect` explicitly directing CSV pipeline resolution seamlessly reliably.
- **Global Theme Washes**: Implemented `table.set_table_style()` and the `--table-bg-color` (`-g`) flag, allowing users to apply universal foregrounds or backgrounds behind table grids natively.
- **Negative Coordinate Architecture**: Re-engineered core rendering logic to accept `-1` indexing natively. Added `--last-col-color` (`-x`), `--last-col-bg-color` (`-y`), `--last-row-color` (`-l`), and `--last-row-bg-color` (`-A`) cleanly.
- **CLI Configuration Workflows**: Added native `--save-theme` workflow generating `~/.config/vistab/themes.json` allowing user-defined themes to persist locally across projects.
- **Python Initialization Expansion**: Enhanced `--show-code` to output method bindings explicitly for data parameters (like `--align` or `--width`), decoupling them from base layout calls.

### Fixed
- **State Corruption on Generator Intersections**: Addressed internal generator pipelines to explicitly prevent purging primary table geometries dynamically on stream intersections.
- **ANSI Terminal Compatibility**: Decoupled chained ANSI escape sequences natively into distinct isolated token parameters (e.g., `\\033[97m\\033[101m`) explicitly resolving attribute clipping in older Windows and WSL terminals.
- **Cell Vertical Alignment Crashes**: Fixed an `unhashable type: list` crash exception strictly mapping within `_splitit()` during boundary sizing logic by explicitly migrating away from `_vislen` bounds.
- **CLI Parser Mappings**: Resolved an internal mapping conflict renaming the internal visual `--row0-color` parameter properly assigning it directly to `--col0-color` (`-0`).
- **Comprehensive API Structuring**: Refactored `docs/API.md` explicitly capturing typing and functionality for 40+ boundaries.

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
