# Evidence - assess documentation (reproducible)

No files were changed. Commands run (all read-only), from repo root:

## Doc surface inventoried
- `ls *.md docs/*.md examples/` -> README.md, AGENTS.md, ARCHITECTURE.md, CHANGELOG.md,
  CONTRIBUTING.md, RELEASING.md, TODO.md, FUNCTIONAL_SPEC.md, docs/API.md, docs/CLI.md;
  examples/{basic_usage,colspan_demo,styled_matrix}.py.
- `wc -l` on the doc set (README 460, API 241, CLI 124, SPEC 95, CHANGELOG 171, CONTRIBUTING 95,
  RELEASING 72).

## Accuracy verified by execution
- `PYTHONPATH=src python examples/basic_usage.py|colspan_demo.py|styled_matrix.py` -> all exit 0.
- README Quick Start snippet run verbatim via `python -c` -> renders a round-header table (OK).

## API coverage sweep
- `grep -oE "def (set_|add_|color_|bold_|draw|stream|sort_by|reset)..." src/vistab.py` -> ~48
  public methods enumerated.
- Looped each against `docs/API.md`; only `set_header_align` and `set_abnormal_row_style` absent.

## Signature accuracy
- `docs/API.md:22` shows `__init__(rows: list = None, header: bool = True, ...)`.
- Actual `src/vistab.py` `__init__(self, rows: Optional[Iterable[Iterable[Any]]] = None,
  header: Optional[Iterable[Any]] = None, ...)`. `docs/API.md:25` prose says
  `Union[bool, List[str]]` - internal contradiction with line 22.

## Recent-feature propagation
- README: `grep -c set_bidi README.md` -> 0; `grep -c '`F`' README.md` -> 0.
- docs/API.md: `grep -c set_bidi` -> 2 (documented). docs/CLI.md: `--no-bidi`, `F=float`
  present.
- docs/CLI.md: `grep -c showcase` -> 0 (README has 3). 
- FUNCTIONAL_SPEC.md sec 4: no set_bidi/set_color/grouped-F hits.

## Integrity / consistency
- Relative `.md` links across README + docs resolve to existing files.
- `grep apply_theme` in docs (excluding deprecation notes) -> none (no deprecated recommendation).
- CHANGELOG [1.2.1] present and complete (from prior release-review reconciliation).

## Sampling / truncation
- Full files read for API.md, CLI.md, the documentation lens, and the IPD template. README /
  FUNCTIONAL_SPEC inspected by targeted grep + section reads, not line-by-line; findings cite
  specific lines/sections.
