[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Vistab Functional Specification

This specification outlines the deterministic constraints, rendering flows, and API invariants governing the `Vistab` library. Any additions or modifications to the core engine must preserve backward compatibility with these definitions.

## 1. Core Principles

- **Lightweight Native Core**: `Vistab` relies on the standard Python library with `wcwidth` calculating explicit text padding limits. Complex external components (e.g., `cjkwrap` for Asian characters) remain optional `[cjk]` extras.
- **Fluent Determinism**: The API state executes serially. Re-running `table.draw()` sequentially with identical datasets and unmodified object state must mathematically result in identical string output bytes.
- **Strict Byte-Sizing**: ANSI escape sequences (colors, text styling) are treated as "invisible" string dimensions during cell boundary width logic calculations.

## 2. Component Pipeline Constraints

### 2.1 Inputs (STDIN & Parsing)

- **Datasets:** The backend `Vistab.add_rows` expects standard Python iterables (e.g. `list[list[str/int]]`).
- **Pipelined Files:** The CLI `vistab file1.csv file2.csv` pipeline implicitly generates multiple iterative tables.
- **STDIN Pipeline & Generative Streams:** Standard pipe structures (`cat data.csv | vistab`) invoke CSV sniffers evaluating parsing logic dynamically. Bypassing rigid buffer allocations, `Vistab.stream()` directly converts infinite stream outputs, triggering immediate formatting evaluations mapped sequentially safely preventing out-of-memory cascades. Constraints demanding explicit pre-knowledge buffers (like `--sort-by`) natively fallback triggering a Caveat Emptor memory penalty iteratively.

### 2.2 Datatype Inference

The structural formatting loop isolates strings based on target datatypes defined in `set_cols_dtype()`:
- `"a"` (Auto): Intelligently casts numeric inputs, stripping `.0` from integers.
- `"f"` (Float): Rounds outputs based on `set_precision(val)`.
- `"t"` (Text): Restricts parsing mechanics, casting the input entirely as text without numeric evaluation.
- `"i"` (Int): Casts uniformly, dropping float decimal blocks entirely.

### 2.3 Constraint Wrappers & Jagged Matrix Rules

- **`max_width` (Line Wraps):** Limits the physical terminal table dimensions. Defaults to `0` (disabled). If enabled, strings are automatically sliced to respect the provided width.
- **`max_cols` / `max_rows`:** Acts explicitly by discarding trailing indices to prevent table matrix bloat.
- **`on_wrap_conflict`:** Defines routing bounds globally for custom styling boundaries. Permissible settings: `"warn"`, `"error"`, `"clip"`, `"overflow"`.
- **Jagged Arrays (`on_short`, `on_long`):** Matrix structures bypassing standard rectangle alignments are resolved intelligently. Missing values align using `--on-short` bounds (`pad`, `skip`, `raise`) and overflow bounds map utilizing `--on-long` constraints (`truncate`, `skip`, `raise`). Outlier structural data boundaries correctly isolate formatting rules visually executing highlighted blocks using `--mark-abnormal`.

## 3. Formatting and Themes Execution Bounds

Themes operate as dictionary structures intersecting with the internal rendering loop. 
User-defined variables passed explicitly via the CLI (like `--align` or `--width`) or specific structural properties must NEVER be cached to `themes.json` using the `--save-theme` logic, as this breaks layout reusability. Settings targeting visual colors, paddings, decorations, and styles are exclusively categorized as theme architectures.

### 3.1 Global `themes.json` Schema

When users execute `--save-theme`, configurations map directly into `~/.config/vistab/themes.json`. The dictionary validates these strictly structured keys:

1. **Global Modifiers**:
   - `style`: (str) Frame mapping (`light`, `bold`, `markdown`).
   - `padding`: (int) Numeric horizontal offset spacing.
   - `decorations`: (int) Internal structural bitmask limits.
2. **Global Architecture Targets**:
   - `table`: Applies default background washes globally across all table coordinates.
   - `border`: Applies colors to the exterior and interior bounding lines.
   - `header`: Applies specific foreground and background targets to the header block.
3. **Array Component Targets**:
   - `row_X`, `col_X`: Targets integers explicitly. E.g. `col_0` overrides the first column.
   - `row_-1`, `col_-1`: Resolves automatically to the dynamic bottom row or final rightmost column.
4. **Color Syntax Definitions**:
   - `fg`: Fore-ground text mappings (e.g., `bright_cyan`).
   - `bg`: Background terminal cell layouts (e.g., `magenta`).
   - `bold` / `italic` / `underline` / `dim`: Boolean definitions activating specific terminal rendering escapes.

---
[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
