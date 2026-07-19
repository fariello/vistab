# Assessment - tests (suite + CI execution)

Verdict: **strong** for testing (148 passing, verified; 80% coverage; meaningful assertions;
deterministic; 1.2.1 features covered). Four narrow, low-risk gap-closers proposed.

IPD written: `.agents/plans/pending/20260719-1530-01-assess-tests.md`

Run ID: 20260719-153031. Version: 1.2.1.

## Evidence (measured, per the lens)
- `unittest discover` -> Ran 148 tests OK. `pytest -q` -> 148 passed.
- `coverage report` -> 80% (2164 stmts, 441 missed).
- 319 meaningful assertions (assertEqual/In/Raises/...) vs 5 bare assertIsNotNone.
- No flakiness constructs (no sleep/random/time/order-dependence).
- Feature coverage: bidi, set_color/--no-color, F/E, colspan, max_width, showcase, non-UTF-8 all
  tested; set_bidi(False) + all on_wrap_conflict modes directly tested.
- 33 byte-exact golden fixtures pin rendered output.

## Uncovered 20% (bucketed)
- Mostly CLI demo/help plumbing (_demo_subject_lines 66, print_coordinate_styles_demo 28, _rev
  24, _apply_clr 19, print_themes_demo 12) + main/arg-handling.
- Behavior-relevant: streaming branches (_process_stream 30, stream/stream_exhaust ~38),
  _ansi_safe_clip 22.

## Top findings
| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| T1 | Medium | Low | testing/QA | Integer `.5` rounding is UNPINNED (only `50.55->51` tested); banker's-rounding behavior could change silently. |
| T2 | Medium | Low | testing | No coverage measurement/reporting anywhere; 80% only known ad hoc. |
| T3 | Low | Low | QA | `_ansi_safe_clip` has no direct CJK+ANSI boundary-clip test. |
| T4 | Low | Low | testing | stream+max_cols truncation and some _process_stream EOF branches uncovered. |

## Proposed plan (summary)
1. Pin `.5` rounding for i/I (coordinate with bugs-assess B1). 2. Add a non-gating coverage
signal (CONTRIBUTING recipe + optional CI print). 3. Direct `_ansi_safe_clip` CJK+ANSI test.
4. Streaming branch tests (max_cols-during-stream, EOF-before-sample).

## Deferred (with reason)
None. All Low Remediation Risk. Did NOT chase coverage on CLI demo/help print paths (low-risk
presentation code; byte-exact fixtures already cover the main demos).

Next step: review the IPD (optionally plan-review; coordinate T1 with bugs-assess B1) and
approve before execution. This workflow does not execute the plan.
