# Evidence - assess tests (reproducible)

No files changed. Read-only, PYTHONPATH=src, from repo root.

## Suite passes (measured)
- `python -m unittest discover tests/` -> "Ran 148 tests in ~6s ... OK".
- `python -m pytest -q` -> "148 passed".

## Coverage (measured)
- `python -m coverage run --source=src -m unittest discover tests/` then `coverage report`
  -> src/vistab.py 2164 stmts, 441 miss, 80%.
- `coverage json` + a script bucketing missing_lines to nearest preceding def:
  _demo_subject_lines 66, _process_stream 30, print_coordinate_styles_demo 28, stream 27,
  _rev 24, _ansi_safe_clip 22, _apply_clr 19, _compute_cols_width 14, _draw_line 13,
  print_themes_demo 12, set_cols_valign 11, stream_exhaust 11, main 11 (top buckets).

## Counts
- `for f in tests/test_*.py: grep -c 'def test_'`: vistab 63, cli 37, regression 30, edge 7,
  demo 5, streaming 4, config 2 => 148. Fixtures: 33.
- Assertions: grep sum of assertEqual/In/NotIn/True/False/Raises/Less = 319; assertIsNotNone = 5.
- Flakiness grep (time.sleep/random./datetime.now/order) -> none relevant (only 'sort'/'border'
  substring hits).

## Feature/behavior coverage spot-checks
- bidi in 2 files; set_color/--no-color in 1; F/E in 1 (F2/F0/negative/E/ non-numeric fallback
  tests present at tests/test_vistab.py ~938-946); colspan in 3; max_width in 1; showcase in 1;
  utf-8 in 4; set_bidi(False) at test_vistab.py:817,840 and CLI test_cli.py:419.
- Rounding: only tests/test_vistab.py:75 (50.55->51); NO .5-boundary test (T1).
- No coverage/--cov in .github/workflows/*.yml or pyproject.toml (T2).

## Sampling
- Full read of the testing lens + IPD template. Coverage numbers are a single deterministic run
  on Python 3.14 (line coverage; branch coverage not separately measured). Conclusions
  (which regions are uncovered, which behaviors are/ aren't pinned) are stable.
