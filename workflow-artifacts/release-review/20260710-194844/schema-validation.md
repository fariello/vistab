# Schema Validation
No formal schema files (no JSON Schema / OpenAPI / protobuf). Implicit data contracts:
- `themes.json` (~/.config/vistab/themes.json): loaded with `json.load` under try/except; malformed file is tolerated (pass). Round-trips via `--save-theme`/`--show-code` and is covered by regression fixtures (`regression_cli_save_theme`, `regression_cli_show_code`). No drift found.
- `.vistab.toml`/config.toml: parsed via guarded tomllib/tomli; keys mapped defensively (`if "x" in v`). No strict schema; malformed handled.
- CSV/TSV input: `csv.Sniffer` with fallback; jagged rows handled via on_short/on_long policies.
No schema syntax errors, no drift, no missing external-input validation beyond documented behavior. `SCH`: none.
