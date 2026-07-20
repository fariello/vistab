# 10 Validation results (all run this session)

- `python -m unittest discover tests/` -> Ran 174 tests ... OK
- `pytest -q` -> 174 passed
- `coverage run --source=src -m unittest discover tests/ && coverage report` -> 80% (TOTAL 2192 stmts, 428 missed)
- `python -m build` + `twine check dist/*` -> both wheel and sdist PASSED
- Wheel contents: single vistab.py module + standard dist-info (LICENSE, NOTICE, METADATA, entry_points). Clean.
- Public API smoke: `from vistab import Vistab, ColSpan`; draw() works.
- CLI smoke: piped CSV renders a table; empty input exits 1 with guidance.
- README first python example: executes and produces correct output. 13 python blocks present.
- pre-commit hooks (secret-scan, EOF, whitespace, yaml, toml) pass on every commit this session.
