[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)

# Vistab API Reference (v1.1.2)

`Vistab` uses a **fluent API**. Almost all manipulation and styling methods return the instance itself (`self`), allowing developers to chain operations:

```python
table = (Vistab()
         .set_title("System Logs")
         .set_style("round-header")
         .bold_header()
         .set_max_rows(10))
```

All standard methods documented below return `Vistab` (via `self`) unless indicated otherwise.
Negative indexing is universally supported for targeting structural coordinates.

---

## 1. Instantiation

### `__init__(rows: list = None, header: bool = True, max_width: int = 0, alignment: str = None, style: str = None, padding: int = None)`
Initializes the Vistab framework.
- **`rows`** `(List[List[Any]])`: 2D array of initial grid cell contents. 
- **`header`** `(Union[bool, List[str]])`: Set to `False` to treat index `0` as standard data. Pass a textual list to force custom headers.
- **`max_width`** `(int)`: Global terminal boundary threshold (0 = infinite).
- **`alignment`** `(str)`: Ordered characters (`'l'`, `'c'`, `'r'`) assigning left/center/right formatting.
- **`style`** `(str)`: Named ASCII/Unicode layout string (e.g., `'round'`, `'light'`, `'markdown'`).
- **`padding`** `(int)`: Base whitespace injected logically around strings.

---

## 2. Data Ingestion & State Modification

### `set_header(array: List[Any])`
Sets the explicit table header list. Passing this forces `self.has_header = True`.

### `add_row(array: List[Any])`
Appends a single dataset line array to the bottom of the table.

### `add_rows(rows: Iterable[Iterable[Any]], header: bool = True)`
Iterates and appends a 2D block. If `header=True` and the table lacks one, index `0` binds to the header element.

### `set_rows(rows: Iterable[Iterable[Any]], header: bool = True)`
Clears existing memory completely replacing structural boundaries with the inserted `rows`.

### `stream(iterable: Iterable[Any], header: bool = True) -> Iterator[str]`
Consumes an infinite generator stream mapping and formatting rows sequentially without buffering matrix arrays into memory.

### `sort_by(col_idx: int, reverse: bool = False, key: callable = None)`
Rearranges row structures internally tracking a dedicated physical column logic.

### `reset()`
Obliterates rendering history, returning internal states functionally matching initial parameters.

---

## 3. Aesthetic Structure & Space Limits

### `set_title(title: str)`
Renders a centered global text label above the primary top border execution.

### `set_style(style_str: str = 'light')`
Instantly reassigns the logical border characters driving table grid formats.

### `set_padding(amount: int)`
Updates internal blank-space padding around column alignments.

### `set_max_cols(max_cols: int)`
Truncates right-most values mapping constraints preventing boundary bloat.

### `set_max_rows(max_rows: int)`
Truncates bottom rows bounding vertical limits.

### `set_max_width(max_width: int)`
Triggers line-wrapping heuristics intercepting text before exceeding terminal boundaries.

### `set_decorations(decorations: int)`
Toggles inner structural grids utilizing bitmask flags (`Vistab.BORDER | Vistab.HEADER | Vistab.VLINES`).

### `set_table_lines(table_lines: str)`
Customizes granular interior lines passing strings targeting intersections.

---

## 4. Alignment & Format Type Coercion

*Parameters evaluating formatting arrays evaluate list structures or single continuous strings (`"lrc"`).*

### `set_cols_width(array: Union[str, List[Any]])`
Forces column geometry adhering mapping integer widths restricting variable expansions.

### `set_cols_align(array: Union[str, List[str]])`
Evaluates explicit mappings resolving horizontal cell justification (`'l'=left`, `'c'=center`, `'r'=right`). Can unpack single-string lists containing the entire sequence (e.g., `["clrcr"]`).

### `set_cols_valign(array: Union[str, List[str]])`
Evaluates positional geometry mapping vertical alignments (`'t'=top`, `'m'=middle`, `'b'=bottom`). Can unpack single-string lists safely (e.g., `["mmbmt"]`).

### `set_cols_dtype(array: Union[str, List[str]])`
Applies robust precision formats wrapping types safely. Can unpack single-string lists (e.g., `["if2e4a"]`). 
*   **Categories**: `'t'=text`, `'f'=float`, `'i'=int`, `'e'=scientific`, `'I'=comma int`.
*   **Automatic (`'a'`)**: evaluates column types systematically scaling uniform numeric sequences via internal cascading hierarchy (`scientific -> float -> integer`), bypassing formatting inconsistencies.
*   **Dynamic Precisions (`'f2'`, `'e4'`)**: Precision overrides structurally integrate directly within dtype arrays (e.g., `["i", "f2", "e4", "a"]`) escaping the global baseline decimal configurations.

### `set_precision(width: int)`
Establishes default global precision logic for all unresolved floats and sequences.

---

## 5. Geometric Wrapping Rules

*Vistab uses coordinate-targeting methods resolving wrapping. By setting `wrap=False` you disable invisible formatting bounds.*

### `set_table_wrap(wrap: bool)` 
Overrides logical evaluations globally protecting geometry structurally.
### `set_row_wrap(row_idx: int, wrap: bool)` 
Locks structural limits horizontally matching boundaries uniformly!
### `set_col_wrap(col_idx: int, wrap: bool)` 
Locks layout parameters vertically.
### `set_cell_wrap(row_idx: int, col_idx: int, wrap: bool)` 
Locks specific cell boundaries protecting manual geometries.

---

## 6. Color Layout Integrations & Thematics

Vistab provides discrete coordinate styling enabling robust parameter modifications elegantly targeting boundaries.
All color keywords map to CLI counterparts (`red`, `green`, `black`, `bright_black`, `none`).

### `apply_theme(theme: Union[str, dict])`
Injects pre-configured algorithms logically matching Zebra-matrices.

```python
table.apply_theme({
    "table": {"bg": "bright_black"}, # Global Target
    "row_-1": {"bg": "magenta"}, # Base End Target
    "header": {"fg": "white"}
})
```

### Coordinate Aesthetic Targeting

*Parameters usually support `fg` (foreground color text), `bg` (background wash layout), and kwargs resolving boolean modifiers (`bold`, `italic`, `underline`, `dim`)*.

#### Global Table Washes
- `set_table_style(fg=None, bg=None, **kwargs)`
- `set_border_style(fg=None, bg=None, **kwargs)`

#### Header Injection
- `bold_header(enable: bool = True)`
- `color_header(fg=None, bg=None)`
- `set_header_style(fg=None, bg=None, **kwargs)`

#### Region Targeting
- `bold_row(row_idx: int, enable: bool = True)`
- `color_row(row_idx: int, fg=None, bg=None)`
- `set_row_style(row_idx: int, fg=None, bg=None, **kwargs)`
- `bold_col(col_idx: int, enable: bool = True)`
- `color_col(col_idx: int, fg=None, bg=None)`
- `set_col_style(col_idx: int, fg=None, bg=None, **kwargs)`
- `set_cell_style(row_idx: int, col_idx: int, fg=None, bg=None, **kwargs)`

#### Algorithmic Zebra Matrix Striping
- `set_alternating_row_style(fg1=None, bg1=None, fg2=None, bg2=None, **kwargs)`
- `set_alternating_col_style(fg1=None, bg1=None, fg2=None, bg2=None, **kwargs)`

---

## 7. Operational Properties & Outputs

### `draw() -> str`
Computes all styling rules and boundary geometries to output the final multi-line string.

### Properties
- `table.has_header` `(bool)`: Disable header tracking without stripping matrix sizes.
- `table.on_wrap_conflict` `(str)`: Defines text-wrapping fallback behaviors (`"warn"`, `"error"`, `"clip"`, `"overflow"`).
- `table.on_short_row` `(str)`: Configures row truncation rules when incoming data matrices are too short (`"pad"`, `"skip"`, `"raise"`).
- `table.on_long_row` `(str)`: Configures jagged bounds handling values that exceed dimension boundaries (`"truncate"`, `"skip"`, `"raise"`).
- `table.sanitize_ansi` `(bool)`: When enabled, strips dangerous cursor manipulation sequences.

---
[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)
