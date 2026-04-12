[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Vistab Roadmap & TODOs

## Architectural Considerations

### 1. Jagged Array / Mismatched Row Routing
Currently, `Vistab` raises an `ArraySizeError` when users input dataset rows that do not match the column count of the first row. In the future, we may need to introduce non-fatal routing logic. 

**Proposed Mechanism:** Introduce an `on_jagged_row = "error" | "expand" | "truncate" | "merge"` configuration.

#### Evaluation of Routing Strategies:

| Strategy | Pros | Cons |
| :--- | :--- | :--- |
| **`"error"` (Current)** | Guarantees perfect geometries and prevents rendering corrupt tables. | Fails on messy CSV arrays and prevents silent rendering tests. |
| **`"expand"`** | Zero data loss. Expands the grid and pads older rows. | Missing alignment/dtype settings for new columns fall back to unknown defaults. |
| **`"truncate"`** | Fast constraint parsing (`row[:size]`). Inherits exact alignment stylings. | Silent data loss. Users might not realize data is being omitted. |
| **`"merge"`** | Preserves all data while maintaining strict column boundaries by appending excess data to the last column. | May break datatype parsing (e.g., merging strings into a float validation column raises exceptions). |
| **`"pad"` (Short Rows)** | Easy to execute (`row + [""] * diff`). Allows missing sparse structures. | Blank injection can break datatype rendering if not caught as `None`. |

### 2. Cell Spanning (Colspan & Rowspan)
Grid geometries currently calculate bounds on a strict row-by-row isolation loop. Spanning cells across boundaries breaks standard parsing logic.

#### Colspan (Target: v1.2.0)
*   **Complexity:** Medium
*   **Architecture Requirements:** Will require introducing a structured data wrapper (e.g., `Vistab.ColSpan("Title", 3)`) that `_check_row_size()` identifies dynamically. During computation, `_compute_cols_width()` must safely coalesce adjacent mapped widths, and `_draw_line()` must bypass interior vertical separators `|` across the span block locally. 
*   **Feasibility:** Aligns natively with the current left-to-right sequential rasterization logic. 

#### Rowspan (Future Consideration)
*   **Complexity:** Extreme / Very High
*   **Architecture Requirements:** Fails instantly within current architecture natively. Terminal output executes strictly top-down. Bridging cells vertically necessitates rewriting the engine into a heavy, globally stateful 2D dimensional canvas buffer to compute overlapping row heights simultaneously.
*   **Feasibility:** Pushes boundary from lightweight parser engine to heavy document renderer. Unlikely in the short term.

[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
