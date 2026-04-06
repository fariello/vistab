# Vistab API Reference

The `Vistab` class utilizes a fluent API. Almost all methods return the class instance (`self`), allowing developers to chain operations:
```python
table.set_title("Logs").bold_header().set_max_rows(10).draw()
```

## Constructor Parameters

```python
Vistab(
    rows=None,          # 2D array of grid cells.
    header=True,        # Boolean or a list of column names.
    max_width=0,        # Global width limit for text wrapping (0 = infinite).
    alignment=None,     # String or list of 'l', 'c', 'r' (left, center, right) for columns.
    style=None,         # String name of the predefined table border style.
    padding=None        # Integer representing left and right padding spaces.
)
```

## Data Ingestion & Manipulation

- `table.header(array)`: Sets the table header.
- `table.add_row(array)`: Inserts a single row array.
- `table.add_rows(array, header=True)`: Iterates over a 2D array and inserts all rows. (If `header=True`, automatically uses index 0 as the header).
- `table.set_rows(array, header=True)`: Clears existing data and replaces it with the new array.
- `table.sort_by(col_idx, reverse=False, key=None)`: Sorts the rows based on the values in a specific column index.
- `table.set_cols_dtype(arrays)`: Coerces structural types for consistent formatting (`'a'=auto`, `'t'=text`, `'f'=float`, `'e'=exp`, `'i'=int`).
- `table.reset()`: Resets the state of the table to its initialization defaults.

## Formatting Constraints

- `table.set_style(style_str)`: Changes the border and structural characters of the table.
- `table.set_cols_width(arrays)`: Forces columns to explicitly adhere to the provided integer widths.
- `table.set_cols_align(arrays)`: Evaluates 'l', 'c', 'r' strings to horizontally align column content.
- `table.set_cols_valign(arrays)`: Evaluates 't', 'm', 'b' strings to vertically align cell content.
- `table.set_max_rows(limit)`: Truncates the table output if it exceeds the row limit.
- `table.set_max_cols(limit)`: Drops right-most columns if they exceed the column limit.

## Thematic Output

- `table.apply_theme(theme_name_str)`: Applies a pre-configured theme layout (like `ocean-index`).
- `table.set_decorations(bitmask)`: Toggles inner structural grids using bitmasks (`Vistab.BORDER | Vistab.HEADER`).

### Coordinate Styling

Vistab supplies direct methods for cell and regional formatting:
- `table.bold_header(enable=True)`
- `table.bold_row(row_idx, enable=True)`
- `table.bold_col(col_idx, enable=True)`
- `table.color_header(fg=None, bg=None)`
- `table.color_row(row_idx, fg=None, bg=None)`
- `table.color_col(col_idx, fg=None, bg=None)`

## Advanced Routing

- `table.has_header = False`: Programmatically ignore the header when drawing the table.
- `table.on_wrap_conflict = "warn"`: Strict security mode that determines how nested table truncation conflicts are handled (`"error"`, `"warn"`, `"clip"`, `"overflow"`).
