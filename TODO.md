# Vistab Roadmap & TODOs

## Architectural Considerations

### 1. Jagged Array / Mismatched Row Routing
Currently, `Vistab` natively throws an `ArraySizeError` when users ingest dataset rows that physically mismatch the column-count established by the first instantiated row. In the future, we may need to introduce non-fatal routing logic. 

**Proposed Mechanism:** Introduce an `on_jagged_row = "error" | "expand" | "truncate" | "merge"` configuration.

#### Evaluation of Routing Strategies:

| Strategy | Pros | Cons |
| :--- | :--- | :--- |
| **`"error"` (Current)** | Guarantees perfect geometries and protects pipelines from rendering corrupt structures natively. | Fails violently on messy CSV arrays and prevents silent rendering tests. |
| **`"expand"`** | Zero data loss. Expands the global grid dynamically and patches older rows symmetrically. | Missing alignment/dtype settings for dynamically born columns will fallback to unknown defaults. |
| **`"truncate"`** | Extremely fast constraint parsing (`row[:size]`). Inherits exact alignment stylings gracefully. | Major silent data loss. Users might not realize backend parameters are being pruned entirely. |
| **`"merge"`** | Preserves all data perfectly while maintaining strict column boundaries (coalesces excess to the last col). | Destroys datatype parsing (e.g., merging strings into a float validation column triggers exceptions). |
| **`"pad"` (Short Rows)** | Trivial to execute (`row + [""] * diff`). Allows missing sparse structures. | Blank injection can ruin datatype rendering if not gracefully caught as a mathematical `None`. |
