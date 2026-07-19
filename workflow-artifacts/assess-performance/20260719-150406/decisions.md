# Decisions & assumptions - assess performance

## Concern / scope
- Concern: performance (render runtime/allocation). Scope: render path in src/vistab.py.
- Assesses SHIPPED 1.2.1 code. Supersedes 2026-07-09 assess-performance (colspan design, pre-impl).

## Method (measured, not guessed)
- cProfile of 3x render of a 1000x8 mixed table; sorted by cumulative time.
- Scaling sweep 500..8000 rows to test for super-linear behavior (found: linear, ~120-130 us/row).
- Inspected the innermost width function (StringLengthCalculator.len -> already lru_cache'd).
- Timed the format_map dict-rebuild cost in isolation (~7.6ms/render).
- Located the 1.2.1 bidi per-cell scan and the span-boundary walk.

## What was intentionally NOT proposed and why (Complexity axis)
- No C-extension, no threading, no whole-row render caching, no algorithmic rewrite: scaling is
  already linear and there is no measured hot quadratic; that complexity is unjustified.
- The 472k isinstance calls are cheap and diffuse; optimizing them adds complexity for unmeasured
  gain. Not proposed.

## Assumptions / open questions
- Whether render speed is a real user pain today or pre-emptive hygiene (the measured ~130 us/row
  is modest). If nobody is hurting, P1-P4 are low-priority polish.
- Benchmark as local tool vs non-gating CI job (recommend local + optional non-gating; runners
  are too noisy for absolute-time assertions).

## Verdict
Adequate. Sound performance posture; proposed changes are safe, byte-identical, evidence-backed.
