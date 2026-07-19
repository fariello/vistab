# Decisions & assumptions - assess bugs

## Concern / scope
- Concern: bugs/correctness (defects in existing behavior). Scope: whole library + CLI, v1.2.1.
- Lens lead personas: QA engineer, software engineer, data-integrity view.

## Method (verified, not inferred)
- 11 targeted reproductions run against real code paths:
  rounding (.5 boundaries), None in each dtype, on_wrap_conflict x4, colspan validation
  (overlap/out-of-range), combine=None strict overwrite, max_width invariant (plain/span/
  long-token/CJK), CJK width alignment at narrow widths, streaming late-wide-row, swallowed-error
  grep (except sites), mutable-default-arg grep.
- Confirmed the rounding mechanism in source (str(int(round(...)))).

## What was intentionally NOT proposed and why
- No concurrency/TOCTOU work: the library is single-threaded pure-Python with no shared mutable
  IO surface; that risk class is essentially absent.
- No broad defensive-programming rewrite: the engine held up under stress; adding guards would be
  complexity without evidence (Complexity axis).
- None-as-"None" (B3) is technically the documented FallbackToText behavior; proposed as a small
  contract refinement, not called a crash.

## Open questions
- B1 rounding policy: round-half-up (changes shipped .5 output; least surprising) vs. keep
  banker's + document. Needs the human's decision; recommend round-half-up.
- B3: empty cell vs. a configurable null placeholder (recommend empty; a setter would be scope
  creep unless requested).

## Verdict
Strong. No crashes/data-loss/correctness failures on reachable paths; only minor nits.
