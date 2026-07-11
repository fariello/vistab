# Section 7 — Implementation (per-phase report)
## What I did
Executed the 4 planned Low-remediation-risk actions:
- A1 (S1-BUG1): bumped version 1.1.3 -> 1.2.0 in pyproject.toml + __version__; moved CHANGELOG [Unreleased] to a dated [1.2.0] section (fresh empty [Unreleased] on top). `vistab --version` now prints 1.2.0.
- A2 (S6-CI1): set requires-python ">=3.9" to match the CI-verified floor (code is 3.7-syntax-safe but 3.7/3.8 untested; raising the floor is the honest fix).
- A3 (S3-T1/T2/T3): added TestColspanInteractions (4 tests) — width distribution, styling parity (span uses source-column style), max_cols clipping a span, multiple spans per row. Verified each behavior against real output before asserting (caught + fixed one wrong assertion in the max_cols test).
- A4 (S4-KD1): added ARCHITECTURE.md — single-module shape, ingest->width->wrap->draw pipeline, security surface, pointers to SPEC + executed decisions.
Committed in two product batches (d8f652b, 50f1b1b). 101 -> 105 tests, all green.
## Why
Fix Bar: all four are Low remediation risk and improve release readiness (version honesty, verified Python floor, regression protection, cold-start orientation).
## What I considered but did NOT do
- D1 (module split): DEFERRED — broad refactor, Medium-High complexity+functionality risk, no release need.
- D2 (type-hint overhaul, S1-Q1): DEFERRED — Medium complexity (large churn) for zero runtime benefit; runtime-harmless, tests green. Not worth diff risk this cycle.
- Did NOT add the 3 CLI TODO features (--delimiter/--auto-width/--json-out): out of scope (feature-adding gold-plating).
- No High/LIVE/MEM findings existed (S2), so nothing to escalate.
- Did not run `python -m build` (tool absent); used pyproject/ast parse validation instead.
