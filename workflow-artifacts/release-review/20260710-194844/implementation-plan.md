# Implementation Plan (Section 7) — RUN 20260710-194844

Consolidated from Sections 1-6. Fix by default; defer only Medium-High+ remediation risk.

## To implement (Low remediation risk → fix now)

| Order | Action ID | Source | Change | RR | Validation |
|---|---|---|---|---|---|
| 1 | A1 | S1-BUG1 | **Version bump 1.1.3 → 1.2.0** in `pyproject.toml` and `src/vistab.py __version__`; move CHANGELOG `[Unreleased]` block to a dated `## [1.2.0]` section (add a fresh empty `[Unreleased]`). Release prerequisite. | Low | `--version` prints 1.2.0; pytest green; CHANGELOG has [1.2.0]. |
| 2 | A2 | S6-CI1 | **Align Python support:** set `requires-python = ">=3.9"` in pyproject to match the CI-verified floor (code is 3.7-syntax-safe but 3.7/3.8 are untested; raising the floor is the honest, simplest fix vs. adding untested matrix rows). | Low | pyproject parses; matches CI matrix floor. |
| 3 | A3 | S3-T1/T2/T3 | **Add colspan regression tests** (tests/test_vistab.py): width-distribution across covered columns; styling parity (span adopts source-column style); max_cols clipping a span; multiple spans in one row. | Low | new tests pass; full pytest green. |
| 4 | A4 | S4-KD1 | **Add a short `ARCHITECTURE.md`** at repo root: single-module structure, the ingest→width→wrap→draw pipeline, key components, and pointers to FUNCTIONAL_SPEC + `.agents/plans/executed/` decision rationale. Thin pointer doc, not duplication. | Low | file present; links resolve. |

## Deferred (Medium-High+ remediation risk — recorded, not fixed)

| Action ID | Source | Why deferred (axis) |
|---|---|---|
| D1 | S5-M1 | Split the 4059-line module — broad refactor, **complexity + functionality** risk, no release need. |
| D2 | S1-Q1 | Overhaul type hints — **complexity** (large churn) for no functional/runtime benefit; runtime-harmless and tests green. Not worth the diff risk this cycle. |

## Notes
- No High/LIVE/MEM findings to fix (S2 found none).
- Backward-compatible release; no migration notes needed.
- After A1-A4: re-run full suite; then Section 8 GO/NO-GO + push plan.
