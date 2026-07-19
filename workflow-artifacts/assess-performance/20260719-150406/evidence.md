# Evidence - assess performance (reproducible)

No files changed. Commands (read-only), PYTHONPATH=src, from repo root:

## Profile
- cProfile over `for _ in range(3): build()` where build() renders a 1000x8 mixed table with
  set_max_width(120). Sorted cumulative; top 20 captured in report.md.

## Scaling sweep
- `for n in [500,1000,2000,4000,8000]:` time a full build+draw of an nx8 mixed table.
- Result: 80/130/256/493/963 ms => ~120-130 us/row flat => linear.

## Code inspection (hot spots)
- src/vistab.py:1073 vislen -> StringLengthCalculator (:335, .len at :375 is @lru_cache(8192)).
- :2579 _str builds format_map dict literal per call (:2588-2600).
- :2671 _get_spanned_boundaries walks each row; called at :2725-2726 per interior hline.
- :2263-2265 (draw) and :2394-2396 (stream) run any(_contains_rtl(str(c)) ...) over all cells.
- :1004 _span_block_width sums a width slice (48048 calls; cheap, left alone).

## Isolated timing
- timeit of the 8-entry format_map dict literal x24000 -> ~7.6 ms (per 1000x8x3 render).

## Sampling
- Full read of the performance lens + IPD template. Profiling/scaling numbers are single-run on
  this machine (indicative, not a committed baseline - which is exactly finding P4). Numbers will
  vary by machine; the LINEAR shape and relative hot-spot ranking are the durable conclusions.
