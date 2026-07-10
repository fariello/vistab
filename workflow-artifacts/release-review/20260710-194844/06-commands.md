# 06 Commands
- `git rev-parse HEAD` / `git status --short` / `git log origin/main..HEAD` — baseline: clean tree, 15 unpushed, head 922e17b. Clean.
- `python --version` -> 3.14.6.
- `wc -l src/vistab.py tests/*.py` -> src 4059 lines; 7 test files.
- `python -m pytest -q` -> 101 passed. Clean.
- `rg TODO|FIXME|HACK|XXX src/vistab.py` -> none.
- `ls .agents/plans/pending .agents/prompts/pending` -> empty (.gitkeep only).
- `rg version pyproject.toml src/vistab.py` -> 1.1.3 both.
