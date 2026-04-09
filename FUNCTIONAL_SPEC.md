[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Vistab Functional Specification

This specification outlines the deterministic constraints, rendering flows, and API invariants governing the `Vistab` library. Any additions or modifications to the core engine must preserve backward compatibility with these definitions.

## 1. Core Principles

- **Zero Dependency Guarantee**: `Vistab` uses the standard Python environment. Complex features (such as `cjkwrap` for wide eastern characters) remain optional `[cjk]` extras.
- **Fluent Determinism**: The API state executes serially. Re-running `table.draw()` sequentially with identical datasets and unmodified object state must mathematically result in identical string output bytes.
- **Strict Byte-Sizing**: ANSI escape sequences (colors, text styling) are treated as "invisible" string dimensions during cell boundary width logic calculations.

## 2. Component Pipeline Constraints

### 2.1 Inputs (STDIN & Parsing)

- **Datasets:** The backend `Vistab.add_rows` expects standard Python iterables (e.g. `list[list[str/int]]`).
- **Pipelined Files:** The CLI `vistab file1.csv file2.csv` pipeline implicitly generates multiple iterative tables in a single session.
- **STDIN (`run_input()`):** If piped via standard input (`cat data.csv | vistab`), the CSV sniffer isolates column separators dynamically (prioritizing commas, tabs, and semicolons).

### 2.2 Datatype Inference

The structural formatting loop isolates strings based on target datatypes defined in `set_cols_dtype()`:
- `"a"` (Auto): Intelligently casts numeric inputs, stripping `.0` from integers.
- `"f"` (Float): Rounds outputs based on `set_precision(val)`.
- `"t"` (Text): Restricts parsing mechanics, casting the input entirely as text without numeric evaluation.
- `"i"` (Int): Casts uniformly, dropping float decimal blocks entirely.

### 2.3 Constraint Wrappers

- **`max_width` (Line Wraps):** Limits the physical terminal table dimensions. Defaults to `0` (disabled). If enabled, strings are automatically sliced to respect the provided width.
- **`max_cols` / `max_rows`:** Acts explicitly by discarding trailing indices to prevent table matrix bloat.
- **`on_wrap_conflict`:** Defines routing bounds globally for custom styling boundaries. Permissible settings: `"warn"`, `"error"`, `"clip"`, `"overflow"`.

## 3. Formatting and Themes Execution Bounds

Themes operate as dictionary structures intersecting with the internal rendering loop. 
User-defined variables passed explicitly via the CLI (like `--align` or `--width`) or specific structural properties must NEVER be cached to `themes.json` using the `--save-theme` logic, as this breaks layout reusability. Settings targeting visual colors, paddings, decorations, and styles are exclusively categorized as theme architectures.

---
[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
