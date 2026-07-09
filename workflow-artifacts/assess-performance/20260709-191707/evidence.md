# Evidence - assess performance (colspan design)

Assessment is reproducible from the files/lines below. No code was changed; no profiler
was run against colspan (unimplemented). Findings are complexity/allocation arguments
anchored to real source lines plus the observed absence of benchmarks.

## Documents read
- `.agents/plans/pending/20260709-colspan-support.md` (the design under assessment; full).
- `.agents/plans/pending/20260709-colspan-support.changes.md` (review history/context).
- `FUNCTIONAL_SPEC.md` — §1 scope, §6 I/O, §11 streaming/memory-bounded contract & sort caveat.
- `AGENTS.md` (contract), `README.md` (present; no principles section).
- Workflow harness: `assess/lenses/performance.md`, `assess/templates/{ipd,run-report,findings.csv}.md`,
  `release-review/fix-decision-policy.md`.

## Source inspected in `src/vistab.py` (hot paths)
- `StringLengthCalculator.len` — `@lru_cache(maxsize=8192)` visible-length memoization: line 224-255.
- `vislen` dispatch (str/bytes -> cached len; else `__len__`): line 892-896.
- `ColorAwareWrapper._break_word` / `wrap_list` (per-char, per-word wrapping): lines 329-407.
- `draw()` — per-cell `_str`, then per-row `_draw_line`, hline per gap: lines 1841-1918
  (esp. formatting loop 1880-1885; row/hline loop 1906-1912).
- `stream()` — bounded-sample geometry, reused; per-line rendering: lines 1920-2062
  (sample capture 1934-1957; one-time `_compute_cols_width` 1983; per-row exhaust 2004-2029).
- `_str` (per-cell format): lines 2134-2163.
- `_check_row_size` (ingestion validation): lines 2165-2198.
- `_build_hline` (junction char per column boundary; reads only `_width`): lines 2219-2248.
- `_len_cell` (split on \n/\t, vislen per part): lines 2250-2266.
- `_compute_cols_width` (O(rows x cols); memoized via `hasattr(self,"_width")`): lines 2268-2343.
- `_draw_line` (inner `for i in range(self.vislen(line[0]))` per display line; `zip(line,_width,_align)`): lines 2471-2590 (inner loop start 2517; per-col 2523).
- `_splitit` (per-cell wrap; `zip(line,_width)`): lines 2592-2656.

## Commands run
- `date +%Y%m%d-%H%M%S` -> run ID `20260709-191707`.
- `git status --short` -> only the two untracked colspan plan files pre-existed; branch `main`.
- `python -c "import ...vistab"` and `python -m pytest -q` (earlier in session) -> import OK; 66 passed, 6 pre-existing unrelated failures in `tests/test_regression.py`.
- `rg` for `_pad`, `_width`, `has_vlines`, `vislen`, `_get_border_ansi` to confirm the
  separator/width arithmetic sites (2238, 2513, 1893-1896).

## Not measured / sampling notes
- No runtime profile of colspan (feature unimplemented) — this is the basis for finding
  P6 (add a benchmark and baseline before implementing).
- `src/vistab.py` is large; inspection focused on the render/ingestion hot paths the
  colspan plan touches, not unrelated CLI/theme code (out of the performance-of-colspan scope).
