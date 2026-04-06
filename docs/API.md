# Vistab API Reference

The `Vistab` sequence strictly utilizes a fluent API schema—almost all mapped methods return the class instance (`self`) actively allowing developers to chain operations aggressively securely:
```python
table.set_title("Logs").bold_header().set_max_rows(10).draw()
```

## Constructor Parameters

```python
Vistab(
    rows=None,          # 2D array of grid cells.
    header=True,        # Boolean boolean masking, or a List mapping formal string names.
    max_width=0,        # Global width limit invoking text wrap boundaries (0 = absolute infinite).
    alignment=None,     # 'lcr' string or list (left, center, right) masking columns.
    style=None,         # Visual string token mapping rendering layout engines.
    padding=None        # Left / right internal whitespace pad.
)
```

## Data Ingestion & Structure Mappings

- `table.header(array)`: Forcibly repopulates the active header object organically natively.
- `table.add_row(array)`: Insert a one-dimensional array gracefully respecting column geometric length constraints.
- `table.add_rows(array, header=True)`: Iterate over massive datasets cleanly extracting arrays. (If `header=True`, silently pops the `index 0` targeting it automatically!).
- `table.set_rows(array, header=True)`: Recursively clears existing datasets seamlessly reloading the state completely safely.
- `table.sort_by(col_idx, reverse=False, key=None)`: Natively targets the backing memory layer mapping arrays chronologically targeting a physical column.
- `table.set_cols_dtype(arrays)`: Coerces structural types specifically targeting outputs safely (`'a'=auto`, `'t'=text`, `'f'=float`, `'e'=exp`, `'i'=int`).
- `table.reset()`: Purges completely resetting logic cleanly to initialization limits natively.

## Window Constraints (Formatting)

- `table.set_style(style_str)`: Restructures physical boundary rendering lines securely targeting templates.
- `table.set_cols_width(arrays)`: Forces strict structural limits seamlessly overriding boundary evaluations securely.
- `table.set_cols_align(arrays)`: Evaluates 'l', 'c', 'r' strings natively evaluating horizontal grid boundaries securely.
- `table.set_cols_valign(arrays)`: Evaluates 't', 'm', 'b' (top/mid/bottom) seamlessly checking internal vertical geometries.
- `table.set_max_rows(limit)`: Limits massive output processing silently safely mapping windows efficiently.
- `table.set_max_cols(limit)`: Aggressively drops final elements preserving console buffer widths.

## Thematic Output Routing

- `table.apply_theme(theme_name_str)`: Loads massive pre-configured geometry striping algorithms securely executing templates statically safely.
- `table.set_decorations(bitmask)`: Toggle inner structural grids seamlessly bypassing layouts tracking constants (`Vistab.BORDER | Vistab.HEADER`).

### Coordinate Fluent Wrappers

Vistab supplies specific one-shot native endpoints avoiding raw backend dictionary injections:
- `table.bold_header(enable=True)`
- `table.bold_row(row_idx, enable=True)`
- `table.bold_col(col_idx, enable=True)`
- `table.color_header(fg=None, bg=None)`
- `table.color_row(row_idx, fg=None, bg=None)`
- `table.color_col(col_idx, fg=None, bg=None)`

## Safety & Collision Parameters

- `table.has_header = False`: Globally bypass structural boundary logic injecting a top mapping cleanly.
- `table.on_wrap_conflict = "warn"`: Strict security geometry mapping targeting nested table rendering crashes securely tracking outputs safely (`"error"`, `"warn"`, `"clip"`, `"overflow"`).
