# Evidence - assess bugs (reproducible)

No files changed. All read-only, PYTHONPATH=src, from repo root.

## Static scans
- `grep -n "except:"` -> none (0 bare excepts). `grep -c "except Exception"` -> 9; inspected the
  two `: pass` sites (3766 themes.json = B2; 4336 save-theme reload = benign fallback to {}).
- `grep` for mutable default args (def ...=[] / ={}) -> none.
- Rounding mechanism: src/vistab.py:2506 `str(int(round(cls._to_float(x))))`, :2514
  `f"{int(round(cls._to_float(x))):,d}"`.

## Reproductions (all via python -c building a Vistab and inspecting draw())
- B1 rounding: i/I of {0.5,1.5,2.5,3.5,2.4,2.6} -> 0/2, 2/2, 2/2, 4/4, 2/2, 3/3 (banker's).
- None handling: a/i/f/t <- None -> "None"; I <- "" -> "" (no crash).
- on_wrap_conflict warn/clip/overflow/error over an unbreakable word at max_width=10 -> all
  behave (error raises VistabOverflowError).
- colspan validation: span-past-end -> ValueError; col/row OOR -> IndexError (clear messages).
- combine=None over a non-empty covered cell -> ValueError (blocks silent overwrite).
- max_width invariant: plain(30)/span(40)/longtoken(20)/cjk(16) -> width == max_width, uniform.
- CJK alignment: max_width 11..15 with '关羽'-heavy cell -> width==mw, uniform, no off-by-one.
- streaming: sample_size=3 then a late very-wide row -> all lines width 9 (fit to sample; the
  documented fixed-geometry tradeoff, not misalignment).

## Sampling
- Full read of the bugs lens + IPD template. Source inspected by targeted grep + section reads of
  the formatters, _str, _get_spanned_boundaries, span validation, and main() config loading.
  Reproductions are single-run and deterministic on this machine (Python 3.14).
