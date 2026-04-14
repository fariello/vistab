[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Vistab Functional Specification

This specification outlines the deterministic constraints, rendering flows, and API invariants governing the `Vistab` library. Any additions or modifications to the core engine must preserve backward compatibility with these definitions.

## 1. Purpose and Scope
Vistab is a lightweight Python library and command-line interface (CLI) tool designed for rendering structured text-based data tables in the terminal. It provides a programmatic, coordinate-based API for styling cell geometries, and it includes robust support for integer-precise ANSI escape sequence rendering. Its scope is bounded to terminal text formatting, relying heavily on native standard library components.

## 2. Core Concepts and Terminology
*   **Vistab**: The core class object that tracks state, applying rendering decorators iteratively across a grid.
*   **Grid**: The two-dimensional internal array of nested rows and columns representing the physical table structure.
*   **Cell**: The specific string boundary intersecting a single row and column.
*   **Theme**: A persistent configuration dictionary modifying border shapes and cell attributes uniformly across the Grid.
*   **ANSI Sanitization**: The internal mechanism (`sanitize_ansi`) that isolates and strips destructive cursor-manipulating ANSI sequences to prevent terminal display hijacking.

## 3. Supported Workflows and Use Cases
Vistab supports three primary operational workflows:
1.  **Programmatic Object Instantiation (`from vistab import Vistab`)**: Developers can build static tables inside Python using `add_rows()`.
2.  **Sequential File Evaluation (`vistab data1.csv data2.csv`)**: The CLI can iterate over direct physical file paths sequentially.
3.  **UNIX UNIX Pipeline Aggregations (`cat file.csv | vistab`)**: The CLI intercepts STDIN streams, feeding them through an internal CSV sniffer logic.

## 4. Public API and Major Internal Responsibilities
The architecture is separated into the execution loop logic and the physical programmatic boundary.

**Major Public APIs:**
*   `Vistab(rows, header)`: The primary constructor routing standard lists into the mapping boundaries.
*   `set_cols_dtype(arrays)`: Handles precise formatting modifications iteratively.
*   `apply_theme(theme_dict)`: Resolves active dictionary style bindings across the target variables.
*   `draw()`: The output loop returning the finalized Unicode strings.
*   `stream()`: Generates lines individually, resolving unbounded data flows.

**Internal Responsibilities:**
*   `_process_stream()`: The CLI parser evaluating configuration rules directly against files and standard IO logic.
*   `_splitit()`: The string manipulator breaking multi-line sentences to respect `max_width` limits while masking ANSI character lengths successfully.

## 5. CLI Behavior and Supported Command Patterns
The CLI utilizes `argparse` to decode operations.
*   **Styles and Borders**: Controlled by `--style`, `--style-def`.
*   **Global Execution Flags**: Handled via `--create-config`, `--show-config`, `--save-theme`, and `--show-code`.
*   **Exit Semantics**: When executing successfully, the tool exits with `0`. If an empty data pipe is transmitted or fatal formatting violations occur, the program exits with code `1` and prints the error matrix to standard error (`sys.stderr`).

## 6. Inputs, Outputs, Side Effects, and Persistence Behavior
*   **Inputs**: Iterables of iterables (`Iterable[Iterable[Any]]`) strings, floats, ints, or valid file paths.
*   **Outputs**: Standard output stream buffers emitting UTF-8 Unicode bytes structurally.
*   **Side Effects**: The CLI execution logic prints directly to STDOUT, triggering direct system terminal buffers.
*   **Persistence**: Vistab does not establish databases except inside categorized user profiles resolving configuration logic: `~/.config/vistab/themes.json` (saved theme states) and `.vistab.toml` (overarching engine defaults).

## 7. Configuration Sources, Defaults, and Precedence Rules
Vistab evaluates visual formatting in a defined order of operations, ranked from highest precedence to lowest:
1.  **Direct CLI Arguments**: Exact variables designated at runtime execution (e.g., `--style bold`, `--width 80`).
2.  **Applied Themes**: Layout rules pulled from the `themes.json` dictionary format.
3.  **TOML Configurations**: Overriding engine defaults pulled sequentially from local or global hierarchical `.toml` definitions (e.g., `./vistab.toml`, `~/.config/vistab.toml`).
4.  **Engine Defaults**: Factory fallback constants (e.g., `style="light"`, `padding=1`).

## 8. Data Models, Schemas, and File Formats
Data processing handles standard structured grids:
*   **Unpacking Modifiers**: API variables evaluating boundaries accept unwrapped lists or strings (e.g., `["if2e"]`).
*   **Datatype Schema (`set_cols_dtype`)**: Supports dynamic parsing routing mechanisms:
    *   `"a"` (Auto): Intelligently casts numeric inputs, upgrading limits based on integer logic.
    *   `"f"` (Float) / `"f2"`: Forces round logic using core Python decimals.
    *   `"t"` (Text): Restricts numerical modifications passing strings unmodified.
    *   `Callable`: Safely evaluates explicit Python functions via `lambda` variables.

## 9. Validation and Error Handling Behavior
*   **Ragged and Jagged Matrices**: Asymmetric matrices throw a structured `ArraySizeError` when evaluated. However, the system allows resolution routing: `--on-short=pad` automatically fills the bounds, and `--on-long=truncate` clips them to map the grids predictably.
*   **File Handling**: Attempting to decode unknown CSV dialects triggers the fallback Sniffer rules without throwing fatal errors. 

## 10. Important Edge Cases and Boundary Conditions
*   **Zero-Width Boundaries**: If `max_width` formatting restrictions establish geometries too small to physically render, the `_draw_horizontal` string execution loop intercepts the exception and throws a generic `ValueError`.
*   **Contiguous Words**: Extremely long words that break standard layout spacing force internal text wrapping constraints. This process respects ANSI-safe string lengths.

## 11. Assumptions, Limitations, and Non-Goals
*   **Caveat Emptor Memory Fallback**: Vistab's `.stream()` routine actively yields memoryless arrays for immediate formatting. However, operations executing grouping restrictions (e.g., `--sort-by`) require allocating the total payload matrix into physical memory to execute sorting.
*   **Non-Goal**: The library avoids handling graphical user interfaces (GUIs), focusing on terminal text execution.

## 12. Security, Privacy, and Safety Considerations
Vistab incorporates an internal `sanitize_ansi` routine. This mechanism protects terminal layout integrity by stripping positional cursor manipulation escapes, preventing potential display hijacking.

## 13. Relationships and Interactions Among Major Components
The interaction between components is linear. The user supplies input parameters and streams to the `_process_stream` CLI loop. These streams are evaluated by the `csv.Sniffer` dialect logic. The resulting data arrays are formatted against the hierarchical configurations, instantiating the core `Vistab` execution engine to draw the final output bytes.
