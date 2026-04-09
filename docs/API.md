# Vistab API Reference (v1.0.3)

`Vistab` uses a **fluent API**. Almost all manipulation and styling methods return the instance itself (`self`), allowing developers to chain operations cleanly:

```python
table = (Vistab()
         .set_title("System Logs")
         .set_style("round2")
         .bold_header()
         .set_max_rows(10))
```

All standard methods documented below return `Vistab` (via `self`) unless explicitly indicated otherwise.
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

### `header(array: List[Any])`
Sets the explicit table header list. Passing this forces `self.has_header = True`.

### `add_row(array: List[Any])`
Appends a single dataset line array targeting the bottom structural row computationally.

### `add_rows(rows: Iterable[Iterable[Any]], header: bool = True)`
Iterates and maps a complex 2D block. If `header=True` and the table lacks one natively, index `0` binds to the header element cleanly.

### `set_rows(rows: Iterable[Iterable[Any]], header: bool = True)`
Clears existing memory completely replacing structural boundaries entirely with the inserted `rows`.

### `sort_by(col_idx: int, reverse: bool = False, key: callable = None)`
Rearranges row structures internally tracking a dedicated physical column iteratively matching native python mapping mechanics safely.

### `reset()`
Obliterates rendering history, returning the internal states safely functionally matching `Vistab` initial parameters smoothly!

---

## 3. Aesthetic Structure & Space Limits

### `set_title(title: str)`
Renders a centered global text label gracefully resting above the primary top border execution natively.

### `set_style(style_str: str = 'light')`
Instantly reassigns the logical border characters driving table grid formats.

### `set_padding(amount: int)`
Updates internal blank-space offsets securely padding column alignments.

### `set_max_cols(max_cols: int)`
Truncates right-most values mapping constraints natively strictly preventing boundary bloat.

### `set_max_rows(max_rows: int)`
Truncates bottom execution safely explicitly bounding vertical output bounds.

### `set_max_width(max_width: int)`
Triggers line-wrapping heuristics mapping constraints actively intercepting text before executing terminal geometry breaks cleanly.

### `set_decorations(decorations: int)`
Toggles inner structural grids natively securely utilizing bitmask flags (`Vistab.BORDER | Vistab.HEADER | Vistab.VLINES`).

### `set_table_lines(table_lines: str)`
Customizes granular interior lines passing strings targeting intersections selectively.

---

## 4. Alignment & Format Type Coercion

*Parameters evaluating formatting arrays natively evaluate list structures or single continuous strings securely (`"lrc"`).*

### `set_cols_width(array: Union[str, List[Any]])`
Forces column geometry adhering firmly globally mapping integer widths cleanly restricting variable expansions.

### `set_cols_align(array: Union[str, List[str]])`
Evaluates explicit mappings resolving horizontal cell justification explicitly (`'l'=left`, `'c'=center`, `'r'=right`).

### `set_cols_valign(array: Union[str, List[str]])`
Evaluates positional geometry mapping vertical alignments organically securely (`'t'=top`, `'m'=middle`, `'b'=bottom`).

### `set_cols_dtype(array: Union[str, List[str]])`
Applies robust precision formats natively wrapping types safely (`'a'=auto`, `'t'=text`, `'f'=float`, `'i'=int`, `'e'=exp`).

### `set_precision(width: int)`
Establishes the default float point accuracy natively resolving boundaries globally intelligently cleanly.

---

## 5. Geometric Wrapping Rules

*Vistab uses coordinate-targeting methods resolving wrapping. By setting `wrap=False` you disable invisible formatting bounds completely securely locking boundaries safely!*

### `set_table_wrap(wrap: bool)` 
Overrides logical evaluations globally protecting geometry structurally wrapping outputs consistently!
### `set_row_wrap(row_idx: int, wrap: bool)` 
Locks structural limits spanning completely horizontally matching boundaries uniformly!
### `set_col_wrap(col_idx: int, wrap: bool)` 
Locks layout parameters vertically explicitly.
### `set_cell_wrap(row_idx: int, col_idx: int, wrap: bool)` 
Locks specific cell boundaries specifically protecting manual geometries structurally.

---

## 6. Color Layout Integrations & Thematics

Vistab provides discrete coordinate styling enabling robust parameter modifications elegantly targeting boundaries explicitly intuitively.
All color keywords map to CLI counterparts natively (`red`, `green`, `black`, `bright_black`, `none`).

### `apply_theme(theme: Union[str, dict])`
Injects pre-configured algorithms logically matching Zebra-matrices natively utilizing configurations natively.

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
Computes all styling rules globally, measuring byte boundaries safely processing geometry logic perfectly outputting the final comprehensive multi-line string natively.

### Properties
- `table.has_header` `(bool)`: Programmatically disable header tracking safely without stripping matrix sizes dynamically correctly cleanly.
- `table.on_wrap_conflict` `(str)`: Explicitly defines evaluation behaviors cleanly mapping routing bounds safely (`"warn"`, `"error"`, `"clip"`, `"overflow"`).
