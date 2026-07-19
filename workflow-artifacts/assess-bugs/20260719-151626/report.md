# Assessment - bugs / correctness (whole project)

Verdict: **strong** for correctness (no crashes, data-loss, or reachable-path failures found;
three minor low-risk nits proposed).

IPD written: `.agents/plans/pending/20260719-1516-01-assess-bugs.md`

Run ID: 20260719-151626. Version assessed: 1.2.1. Method: 11 targeted reproductions, verifying
each suspected issue by running the actual code path (per the lens), not inferring.

## Verified correct (no change proposed)
- max_width never exceeded (plain/colspan/long-token/CJK); every line width-uniform.
- CJK 2-wide alignment correct at narrow max_width (11-15); no off-by-one.
- All on_wrap_conflict modes (warn/clip/overflow/error) behave.
- set_cell_span validation raises clear errors; combine=None blocks silent overwrite.
- Streaming holds sampled geometry (late wide row fit, not misaligned) - documented tradeoff.
- No bare except, no mutable default args, no swapped-arg/off-by-one in the width/wrap core.

## Top findings
| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| B1 | Medium | Low | QA | Integer format uses Python round() = banker's rounding: i(0.5)=0, i(2.5)=2, i(3.5)=4. Surprising and undocumented. |
| B2 | Low | Low | engineer | Malformed ~/.config/vistab/themes.json is silently swallowed (except: pass); user gets no warning their config failed. |
| B3 | Low | Low | QA | None in a numeric column renders the literal "None" rather than blank/placeholder. |

## Proposed plan (summary)
1. B1: decide + document integer rounding (recommend round-half-up for least surprise); pin with tests.
2. B2: warn to stderr on unparseable themes.json instead of silent pass.
3. B3: render None in numeric columns as empty (not "None").

## Deferred (with reason)
None. All Low Remediation Risk.

Next step: review the IPD (optionally run plan-review; B1 needs the rounding-policy decision)
and approve before execution. This workflow does not execute the plan.
