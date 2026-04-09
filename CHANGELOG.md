# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-08

### Added
- **Global Theme Washes**: Implemented `table.set_table_style()` and the `--table-bg-color` (`-g`) flag, allowing users to apply universal foregrounds or backgrounds behind table grids natively.
- **Negative Coordinate Architecture**: Re-engineered core rendering logic to accept `-1` indexing natively. Added `--last-col-color` (`-x`), `--last-col-bg-color` (`-y`), `--last-row-color` (`-l`), and `--last-row-bg-color` (`-A`) cleanly.
- **CLI Configuration Workflows**: Added native `--save-theme` workflow generating `~/.config/vistab/themes.json` allowing user-defined themes to persist locally across projects.
- **Python Initialization Expansion**: Enhanced `--show-code` to explicitly output explicit method bindings for data-specific dimensions (like `--align` or `--width`), cleanly decoupling them from reusable color targets.

### Fixed
- **CLI Parser Mappings**: Resolved an internal mapping conflict renaming the visual `--row0-color` flag internally properly assigning it functionally to `--col0-color` (`-0`) directly mapping the physical columns visually flawlessly.
- **Comprehensive API Structuring**: Completely refactored `docs/API.md` documenting the entire suite explicitly capturing typing and functionality for 40+ methods organically mapping Python project quality boundaries safely.

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
