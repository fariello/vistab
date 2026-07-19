# Assessment - performance (render path)

Verdict: **adequate** for performance (linear-scaling, no algorithmic/I/O/concurrency issues;
a few low-risk, profile-evidenced micro-optimizations proposed).

IPD written: `.agents/plans/pending/20260719-1504-01-assess-performance.md`

Run ID: 20260719-150406. Version assessed: 1.2.1. Supersedes the 2026-07-09 assess-performance
(which reviewed the colspan DESIGN before it was implemented); this assesses shipped code.

## Measured evidence
- cProfile (3x render, 1000x8 mixed, max_width=120): 1.380s. Top: _draw_line 0.606, _splitit
  0.346, _compute_cols_width 0.200, _str 0.154 (24000 calls), _len_cell 0.149, vislen 0.084,
  _span_block_width 0.080, wrap_list 0.078.
- Scaling: 500->80ms, 1000->130ms, 2000->256ms, 4000->493ms, 8000->963ms => flat ~120-130
  us/row => LINEAR. No super-linear term.
- StringLengthCalculator.len already lru_cache'd. No hot quadratic. No I/O/network/threads.

## Top findings
| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| P1 | Low | Low | engineer | `_str` rebuilds the constant `format_map` dict every cell (24000 calls, ~6% of render). |
| P2 | Low | Low | engineer | Bidi gate regex-scans every cell each draw even for pure-ASCII / set_bidi(False). |
| P3 | Low | Low | engineer | `_get_spanned_boundaries` walks rows even when the table has no spans. |
| P4 | Medium | Low | architect | No committed benchmark baseline to prove an optimization or catch a regression. |

## Proposed plan (summary)
1. P4: add a deterministic micro-benchmark harness (before/after tool; not CI-gated on absolute time).
2. P1: hoist `format_map` to a build-once constant (byte-identical output).
3. P3: table-level `_has_spans` fast path to skip span-boundary scanning in the common case.
4. P2: skip/early-exit the RTL scan when bidi off or on first hit; single pass.

## Deferred (with reason)
None. All Low Remediation Risk. No C-extension/threading/row-caching/algorithmic rewrite
proposed (no evidence of cost to justify that complexity).

Next step: review the IPD (optionally run plan-review) and approve before execution. This
workflow does not execute the plan.
