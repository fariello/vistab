# Guiding-Principles Assessment (universal fallback; no repo principles file)

No `GUIDING_PRINCIPLES.md` in repo → assessed against the universal fallback.

| Principle | Adherence | Evidence |
|---|---|---|
| **Intuitive / self-documenting (learn as you go)** | **Strong** | Natural-language CLI verbs (`vistab show styles`), `--help`/`--help-colors`/`--help-advanced`, self-documenting error tips (format error prints align/valign/dtype hints; unknown style/theme errors point at `vistab show styles`/`show themes`). Fluent API with descriptive names (`set_header_span`, `combine=`). |
| **Solve general case / configurable over hardcoded** | **Strong** | Coordinate styling API, theme system, config precedence (CLI>theme>TOML>defaults), `on_short_row`/`on_long_row`/`on_wrap_conflict` policies, `combine` separator configurable. Colspan is a general mechanism, not special-cased. |
| **KISS** | **Adequate** | Single dependency (`wcwidth`); no over-engineering. Counter-note: single 4059-line module is large (a natural but not required split); pre-parse CLI dispatch chosen over heavier argparse subparsers (KISS-aligned). |
| **Honest documentation** | **Strong** | Docs match code (verified S4); `apply_theme` honestly marked deprecated; TODO.md honestly marks colspan done and rowspan/CLI-ideas as future with rationale; SPEC documents real limitations (sort+stream memory). |

**Verdict:** Adheres well to the fallback principles. No `GP` violations. Optional: a short `GUIDING_PRINCIPLES.md` capturing these (KD, low value given consistent observable adherence).
