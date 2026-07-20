# 01 Repository inventory
- Type: pure-Python library + CLI (single module src/vistab.py, ~4500 lines). Dep: wcwidth; optional cjk extra (cjkwrap); dev extra: pytest, coverage.
- Public API: Vistab class + ColSpan; CLI `vistab` (entry point) with verbs (show showcase, --no-color, --no-bidi, --version).
- Tests: 7 files in tests/ (vistab, cli, regression, edge, streaming, config, demo) + 34 golden fixtures. 174 tests.
- Docs: README, docs/API.md, docs/CLI.md, FUNCTIONAL_SPEC.md, ARCHITECTURE.md, CHANGELOG.md, CONTRIBUTING.md, RELEASING.md.
- Decisions/ADRs: .agents/plans/executed/ IPDs (dated) serve as ADRs; no separate DECISIONS.md (established convention).
- Backlog: TODO.md (roadmap). No pending plans, no staged prompts.
- Principles doc: none -> fallback.
- CI: test.yml (matrix 3.9-3.13 ubuntu+windows + non-gating benchmark/coverage), secret-scan.yml (gitleaks). pre-commit configured.
- Packaging: pyproject.toml, Apache-2.0, LICENSE+NOTICE, requires-python>=3.9. Version 1.2.1 (unreleased; PyPI latest 1.2.0; v1.2.1 not tagged).
