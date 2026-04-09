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

[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
