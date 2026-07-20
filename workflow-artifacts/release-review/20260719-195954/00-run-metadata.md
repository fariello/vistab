# 00 Run Metadata

- Run ID: 20260719-195954
- Workflow: release-review
- Agent/model: its_direct/pt3-claude-opus-4.8-1m-us
- Repository: /home/gfariello/VC/vistab
- Project: vistab (pure-Python terminal-table library + CLI)
- Git: branch `main`, head `fca192c` at run start
- Remote: origin git@github.com:fariello/vistab.git (GitHub)
- Working tree: clean (only `tmp/` untracked, gitignored)
- Unpushed commits at start: 18 (ahead of origin/main)
- Version under review: pyproject/__version__ = 1.2.1 (PyPI latest published = 1.2.0; 1.2.1 not yet tagged/released)
- Environment: Python 3.14 venv at /home/gfariello/venv/p3.14; tests via `PYTHONPATH=src python -m unittest discover tests/` and `pytest`.

## Pre-flight gate (Section 1)
- To be assessed after Section 1 discovery.

## Prior session context (input, not a review target)
This run follows an extended session that executed several `/assess` -> IPD -> plan-review ->
execute cycles (documentation, self-documentation, bugs B1/B2/B3, performance, empty-table
draw() fix E1, tests T1-T5). Those IPDs are in `.agents/plans/executed/`. This release-review
independently audits the resulting tree; it does not trust the prior work on faith.
