# Decisions & assumptions - assess tests

## Concern / scope
- Concern: testing rigor/completeness. Scope: tests/ + CI execution, v1.2.1.
- Lens lead personas: testing/regression expert, QA, software engineer.

## Method (evidence, not self-report - per the lens)
- Ran the suite two ways (unittest discover + pytest): 148 pass.
- Ran coverage (source=src): 80%, 441 missed lines; bucketed missed lines to owning functions.
- Grepped feature coverage and assertion quality; scanned for flakiness constructs.
- Verified specific behaviors are pinned (bidi, F/E incl. F0/negative/non-numeric, colspan
  max_width, non-UTF-8 stdio, on_wrap_conflict modes, set_bidi(False)).

## What was intentionally NOT proposed and why (Complexity axis)
- Not chasing coverage on CLI demo/help print paths (_demo_subject_lines, print_*_demo): low-risk
  presentation code, main demos already fixture-pinned. Testing them for line% is number-chasing.
- No property-based/e2e/load testing proposed: overkill for a small deterministic string lib;
  the golden-fixture + unit approach is appropriate.
- No brittle/low-value tests found to remove.

## Open questions
- T2 coverage: local + non-gating CI print now (recommended) vs an eventual gate (risks churn).
- T1 depends on the bugs-assess B1 rounding decision; if B1 changes rounding, do T1's test update
  as part of B1 rather than pinning about-to-change behavior. Sequence them together.

## Verdict
Strong. High-confidence suite; proposed additions are narrow gap-closers, all low risk.
