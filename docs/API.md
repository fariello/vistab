[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)

# Vistab API Reference

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

### `__init__(rows: Iterable[Iterable] = None, header: Union[bool, Iterable] = None, max_width: int = 0, alignment: str = None, style: str = None, padding: int = None, title: str = None, max_rows: int = 0, max_cols: int = 0, theme: Union[str, dict] = None)`
Initializes the Vistab framework.
- **`rows`** `(List[List[Any]])`: 2D array of initial grid cell contents. 
- **`header`** `(Union[bool, List[str]])`: Set to `False` to treat index `0` as standard data. Pass a textual list to force custom headers.
- **`max_width`** `(int)`: Global terminal boundary threshold (0 = infinite).
- **`alignment`** `(str)`: Ordered characters (`'l'`, `'c'`, `'r'`) assigning left/center/right formatting.
- **`style`** `(str)`: Named ASCII/Unicode layout string (e.g., `'round'`, `'light'`, `'markdown'`). Run `vistab --demo styles` to view all available styles.
- **`padding`** `(int)`: Base whitespace injected logically around strings.
- **`title`** `(str)`: Optional centered title printed above the table.
- **`max_rows`** `(int)`: Truncates bottom rows bounding vertical limits (0 = infinite).
- **`max_cols`** `(int)`: Truncates right-most columns to restrict horizontal bounds (0 = infinite).
- **`theme`** `(Union[str, dict])`: A named theme (e.g., `'ocean'`) or a custom style dictionary to apply post-construction.

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

### `set_header_span(col_idx: int, colspan: int, combine: Optional[str] = " ")`
Sets the column span of a specific header cell at the given physical column index (negative indexing supported).
- **`combine`** `(Optional[str])`: Separator used to merge non-empty covered cell values left-to-right (default is `" "`). If `""`, joins with no separator. If `None` (strict mode), raises `ValueError` if any covered cell is non-empty. Raises `TypeError` if `combine` is a non-string/non-None type. Raises `IndexError` for out-of-range columns, and `ValueError` for overlaps or placeholder targets. Merged cells are pre-formatted strings, so column-specific `set_cols_dtype` rules do not re-apply to them.

### `set_cell_span(row_idx: int, col_idx: int, colspan: int, combine: Optional[str] = " ")`
Sets the column span of a specific data cell at the given physical row and column coordinate (negative indexing supported).
- **`combine`** `(Optional[str])`: Separator used to merge non-empty covered cell values left-to-right (default is `" "`). If `""`, joins with no separator. If `None` (strict mode), raises `ValueError` if any covered cell is non-empty. Raises `TypeError` if `combine` is a non-string/non-None type. Raises `IndexError` for out-of-range rows/columns, and `ValueError` for overlaps or placeholder targets. Merged cells are pre-formatted strings, so column-specific `set_cols_dtype` rules do not re-apply to them.

### `ColSpan(value: Any, colspan: Optional[int] = None, span: Optional[int] = None)`
Wrapper object passed inside headers or rows to declare inline column spans. Accept both `colspan` and `span` parameter keywords (with the second positional argument mapping to `colspan/span`). Spans `< 1` are rejected with `ValueError` (where `colspan=1` is a no-op).

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

### `set_header_align(array: Union[str, List[str]])`
Sets the horizontal alignment for the header row independently of the body columns (same codes as `set_cols_align`: `'l'`, `'c'`, `'r'`). Use this when the header should align differently from its data (e.g. centered headers over right-aligned numbers).

### `set_cols_dtype(array: Union[str, List[str]])`
Sets the per-column data type / formatting. Accepts a string (one code per column, e.g.
`"tif2"`), a list of codes (e.g. `["t", "i", "f2"]`), or a single-string list (`["tif2"]`).

*   **Codes**:
    * `'a'` = **auto**: pick the most appropriate type per column (the default). Cascades scientific -> float -> integer for uniform numeric columns.
    * `'t'` = **text**: no numeric coercion.
    * `'i'` = **int**: `123456` (fractional values round half away from zero: `2.5` -> `3`, `-2.5` -> `-3`).
    * `'I'` = **int with thousands separators**: `123,456` (integer only; decimals are rounded away, half away from zero: `2.5` -> `3`, `-2.5` -> `-3`).
    * `'f'` = **float**: fixed-point decimal, e.g. `123456.79`.
    * `'F'` = **float with thousands separators**: e.g. `123,456.79`.
    * `'e'` = **scientific/exponential**: e.g. `1.23e+05`.
    * `'E'` = **scientific with thousands separators**.
*   **Precision suffix**: numeric codes accept a decimal-place count, e.g. `'f2'` -> `123456.79`, `'F2'` -> `123,456.79`, `'e4'`. Without a suffix, the global `set_precision(n)` value is used.
*   **A callable** `value -> str` may be given per column for any format the built-in codes do not cover. This is the escape hatch for **comma-grouped decimals and currency**, which the single-letter codes do not produce:

```python
# Comma-grouped float with 3 decimals -> "123,456.789"
table.set_cols_dtype([lambda v: f"{float(v):,.3f}"])

# US dollars, comma-grouped, 2 decimals -> "$123,456.79"
table.set_cols_dtype([lambda v: f"${float(v):,.2f}"])

# Other currencies: you supply the symbol/placement, vistab does not guess a locale
table.set_cols_dtype([lambda v: f"\u20ac{float(v):,.2f}"])   # euro prefix:  \u20ac123,456.79
table.set_cols_dtype([lambda v: f"{float(v):,.2f}\u00a0kr"]) # suffix:       123,456.79 kr
# Negatives in parentheses (accounting):
table.set_cols_dtype([lambda v: (f"({abs(float(v)):,.2f})" if float(v) < 0 else f"{float(v):,.2f}")])
```

> **Note:** use `'F'` for grouped decimals (`123,456.79`) and `'I'` for grouped integers.
> There is no built-in currency type; use a callable (above) for currency, since vistab does
> not guess a locale.

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

### `set_theme(theme: Union[str, dict])`
Injects pre-configured algorithms logically matching Zebra-matrices. (Note: `apply_theme` is supported as a deprecated alias for backward compatibility).

```python
table.set_theme({
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
- `set_abnormal_row_style(fg=None, bg=None, **kwargs)` - style applied to rows flagged abnormal by the jagged-row handlers (a short/long row that was padded or truncated), so malformed input is visually distinguishable. The CLI exposes this via `--mark-abnormal`.
- `set_alternating_row_style(fg1=None, bg1=None, fg2=None, bg2=None, **kwargs)`
- `set_alternating_col_style(fg1=None, bg1=None, fg2=None, bg2=None, **kwargs)`

#### Rendering Toggles

### `set_color(enabled: bool = True) -> Vistab`
Enables or disables vistab's own ANSI color/style output. When disabled, themes,
coordinate styles, and borders render in plain monochrome; ANSI you put in cell content
yourself is not stripped. Chainable.

### `set_bidi(enabled: bool = True) -> Vistab`
Enables (default) or disables bidi-safe rendering of right-to-left (RTL) text. When any
cell contains RTL script (Arabic, Hebrew, etc.), vistab wraps each cell's content in
Unicode LTR isolates (`U+2066`..`U+2069`) so the terminal's bidirectional algorithm does
not reorder the whole line and flip the columns. The RTL text still reads correctly
right-to-left inside its cell. The isolate characters are zero-width, so column widths and
alignment are unchanged, and tables with no RTL content are byte-identical (unaffected). A
few terminals ignore isolates; use `set_bidi(False)` if yours does. Chainable.

---

## 7. Operational Properties & Outputs

### `draw() -> str`
Computes all styling rules and boundary geometries to output the final multi-line string. A truly
empty table (no header and no rows) returns `""`. To draw an empty one-cell box instead, give the
table a present-but-empty structure, e.g. `Vistab().set_header([""])` or `add_row([""])`.

### Properties
- `table.has_header` `(bool)`: Disable header tracking without stripping matrix sizes.
- `table.on_wrap_conflict` `(str)`: Defines text-wrapping fallback behaviors (`"warn"`, `"error"`, `"clip"`, `"overflow"`).
- `table.on_short_row` `(str)`: Configures row truncation rules when incoming data matrices are too short (`"pad"`, `"skip"`, `"raise"`).
- `table.on_long_row` `(str)`: Configures jagged bounds handling values that exceed dimension boundaries (`"truncate"`, `"skip"`, `"raise"`).
- `table.sanitize_ansi` `(bool)`: When enabled, strips dangerous cursor manipulation sequences.

---
[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)
