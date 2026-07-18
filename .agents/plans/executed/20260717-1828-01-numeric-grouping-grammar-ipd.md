# Implementation Plan - Numeric formatting grammar: thousands grouping for floats/exp (and an optional literal prefix/suffix)

Status: executed (2026-07-17). Shipped as **1.2.1** (patch bump). Added `F`/`E` codes +
`_fmt_comma_float`/`_fmt_comma_exp` + format_map, `F`/`E` in COLUMN_DTYPES (tokenizer
UNCHANGED); 7 new tests (grouping, negatives, non-numeric fallback, bare-F global precision,
f/F/i/I distinctness, existing-strings-unchanged); docs synced (README/API/CLI + _dtype_help);
CHANGELOG [1.2.1]; version bumped to 1.2.1 and README/pyproject URLs repinned to v1.2.1;
regenerated the regression fixture for the grown help text. Full suite 146 green; build +
twine check PASS. OQ decisions taken as recommended: letter `F`, include `E`, currency stays
a callable.

> Version correction (2026-07-17): the plan text below proposed 1.3.0 on the mistaken premise
> that 1.2.0 was not on PyPI. It IS published (verified via `curl https://pypi.org/pypi/vistab/json`).
> Because the F/E codes are purely additive and backward-compatible, the release is a PATCH bump
> to 1.2.1, not a minor bump to 1.3.0. References to "1.3.0" in the planning sections below are
> superseded by 1.2.1. The comma overload (first plan-review) reframed the grammar to the collision-free
`F`/`E` codes; the second plan-review verified all `path:line` claims and added edge-case test
coverage, named the release version, and hardened the execution gate.

## Workflow history
- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004.

## Plan-review findings (2026-07-17, verified against src/vistab.py:1912)

Re-opened the tokenizer. `set_cols_dtype` does `re.findall(r'[a-zA-Z]\d*', array.replace(",", ""))`.
Verified empirically:
- `"a,t,f4,i"` and `"atf4i"` tokenize IDENTICALLY to `['a','t','f4','i']`. **Commas are purely
  decorative today** (stripped before tokenizing), NOT structural separators.
- `"f,2"` tokenizes to `['f2']`: a grouping comma would be SILENTLY SWALLOWED (grouping lost,
  no error). This is the F1 blocker.

Implications that change the recommendation:
- **F1 (BLOCKER):** proposing `,` as the grouping flag directly collides with the existing
  decorative-comma behavior. Making `,` structural (the "field-split" fix) would change how
  every existing comma-containing dtype string parses (e.g. `"a,t,f4,i"`), risking a silent
  behavior change for current users. Overloading `,` is the wrong primitive.
- **F2 (HIGH):** RECOMMENDATION CHANGED. Use a grouping flag that does NOT collide with the
  decorative comma. Options, best first:
  1. A distinct flag char that is not stripped and not a code letter or digit, e.g. `_`
     (underscore, which Python format specs ALSO accept as a grouping option: `f"{v:_.2f}"`
     yields `123_456.79`) OR a dedicated grouping letter. But underscore-grouping produces
     `_` not `,`; not what users want visually.
  2. **A new single code letter for "grouped float", e.g. `F` (capital) mirroring how `I` is
     "grouped int".** `F2` -> `123,456.79`, `F` uses global precision. This is the most
     intuitive and collision-free: it parallels the existing `i`/`I` pairing (`f`/`F`), needs
     NO change to the comma-stripping tokenizer, and cannot regress any existing string.
     Add `E` similarly if grouped-exp is wanted. THIS IS THE NEW RECOMMENDATION.
  3. Keep `,` but only honor it as grouping when it appears BETWEEN a letter and digits within
     a single token; rejected because the pre-strip destroys that information and reintroducing
     it is fragile.
- **F3 (MEDIUM):** the drift-guard test and `COLUMN_DTYPES` single-source-of-truth must be
  extended to include any new letters (`F`/`E`), keeping `_dtype_help()` authoritative.
- **F4 (LOW):** currency affordance (Open Question 1) remains correctly deferred to callables;
  no change.

Net: the ORIGINAL `f,2` grammar in the body below is superseded by the `F`/`E` grouped-code
approach. The body is retained for context but read it through the lens of these findings; the
"comma overload" section correctly identified the risk, the resolution is now "don't use a
comma, add a `F` code" rather than "make commas structural".

Today the built-in column data-type codes cannot produce the two most-requested numeric
formats: a **grouped float with decimals** (`123,456.789`) and **currency** (`$123,456.79`).
`I` groups integers only; `f2`/`e4` give decimals without grouping; there is no currency
type. The only current way to get these is a per-column callable (library API only), which
CLI users cannot use. This plan adds a small, general grammar extension so grouped decimals
work from a string code (and therefore from the CLI), plus an optional literal prefix/suffix
so currency is expressible without vistab guessing a locale.

## Prose convention

No em dashes in authored prose (repo/AGENTS.md convention); use periods, commas, colons, or
parentheses.

## Motivation and audience

- Novice/CLI user: wants "commas and 2 decimals" and "dollars" without writing Python. A
  string code reachable from `--dtype` serves them.
- Power user: wants no artificial ceiling. A general format-spec-ish grammar plus a literal
  symbol beats a hardcoded currency list (which is opinionated, locale-dependent, and never
  complete). We deliberately do NOT build a currency/locale subsystem (KISS).
- The callable path already covers everything for library users and stays as the ultimate
  escape hatch; this plan makes the common cases reachable as string codes / on the CLI.

## Current behavior (verified in `src/vistab.py`)

- Valid codes and the enumeration live in `COLUMN_DTYPES` / `_DTYPE_CODES` / `_dtype_help()`
  (module level). Formatters: `_fmt_int`, `_fmt_comma_int` (`f"{...:,d}"`), `_fmt_float`
  (`'%.*f'`), `_fmt_exp` (`'%.*e'`), `_fmt_text`, `_fmt_auto`.
- Token parsing: `set_cols_dtype` splits a string with `re.findall(r'[a-zA-Z]\d*', ...)`
  (`src/vistab.py` ~1900) and validates `a[0] in _DTYPE_CODES`. Precision is extracted in
  `_str` (~2580) via `dtype[1:].isdigit()` -> `n = int(dtype[1:])`, `dtype = dtype[0]`.
- So a token is currently `<letter><digits?>`. Any grammar extension must update BOTH the
  `set_cols_dtype` regex/validation AND the `_str` precision/flag extraction, and keep the
  `COLUMN_DTYPES`/`_dtype_help()` single-source-of-truth in sync.

## Proposed grammar (REVISED per plan-review F1/F2: use a code letter, not a comma)

1. **Grouped-float code `F`, mirroring `i`/`I`.** Add capital `F` = "float with thousands
   separators", so the pairing is symmetric: `f`->`123456.79`, `F`->`123,456.79`,
   `i`->`123456`, `I`->`123,456`. Precision suffix works as usual: `F2` -> `123,456.79`, `F`
   uses the global `set_precision`. Optionally add `E` = grouped scientific for consistency
   (low value; include only if trivial).
   - This is collision-free: it needs NO change to the comma-stripping tokenizer, so every
     existing dtype string (including decorative-comma strings like `"a,t,f4,i"`) parses
     byte-identically. It is also the most intuitive: users already know `I` is "grouped int".
   - REJECTED alternative: `f,2` (comma flag). The tokenizer strips commas
     (`src/vistab.py:1912`), so `"f,2"` silently becomes `f2` and grouping is lost; making the
     comma structural would change existing parsing. See findings F1/F2.
2. **Optional literal prefix/suffix for currency (decide in review, see Open Questions).**
   Two candidate shapes, pick one:
   - (a) A separate per-column affordance: `set_cols_affix(["$", ""], side="prefix")` or
     kwargs on `set_cols_dtype`. Keeps the dtype token clean.
   - (b) Inline literals in the token, e.g. `"$f,2"` / `"f,2 kr"` (suffix). More compact but
     complicates the token grammar/regex and currency symbols collide with the parser.
   Recommendation: prefer NOT inlining arbitrary literals into the dtype token (regex and
   symbol collisions). If currency-as-code is wanted, do (a). Otherwise document callables for
   currency and ship only the grouping flag (1). The grouping flag alone is the high-value,
   low-risk core.

## Proposed implementation (`F`/`E` grouped codes; tokenizer UNCHANGED)

- Add `F` (and optionally `E`) to `COLUMN_DTYPES` / `_DTYPE_CODES` with a clear label and
  explanation. Because the tokenizer is `[a-zA-Z]\d*`, `F`/`E`/`F2` already tokenize correctly
  with NO regex change. The comma-strip stays as-is (decorative commas keep working).
- Add formatters: `_fmt_comma_float` = `f"{cls._to_float(x):,.{n}f}"` and, if included,
  `_fmt_comma_exp` = `f"{cls._to_float(x):,.{n}e}"`. Register `'F'`/`'E'` in the `format_map`
  in `_str` (~2568). Precision `n` extraction at ~2580 already handles `F2` (`dtype[1:].isdigit()`).
- `_fmt_auto` unaffected (auto never emits `F`; users opt in explicitly).
- Update `_dtype_help()` (single source of truth) so all three surfaces document `F`/`E`.
- CLI: no new flag; `--dtype "tF2"` flows through unchanged. No comma involved, so no
  arg-splitting hazard.
- Currency stays a callable (documented in Phase A); this plan does not add a currency code.

## Invariants / anti-regression

- All existing dtype strings render byte-identically: `f2`, `e4`, `i`, `I`, `t`, `a`, and
  comma-decorated strings like `"a,t,f4,i"` (== `"atf4i"`) must be unchanged. Since the `F`/`E`
  codes add NEW letters and the tokenizer/comma-strip is untouched, this holds by construction;
  pin it with characterization tests anyway to lock the guarantee.
- Callable dtypes unchanged.
- Grouped codes inherit the existing `FallbackToText` behavior: a grouped code over a
  non-numeric cell must render as text (like `I` does today), not crash (verified: `I` over
  `"hello"` renders `hello`).
- Bare `F`/`E` (no precision suffix) use the global `set_precision` default, exactly as bare
  `f`/`e` do (verified: bare `f` renders with the default precision, does not error).
- `_dtype_help()`/`COLUMN_DTYPES` remain the single source of truth; the drift-guard test
  (`test_dtype_help_enumeration_matches_format_map`) still holds with `F`/`E` added to BOTH
  `COLUMN_DTYPES` and `format_map`.

## Verification

- **Regression pins (byte-identical):** `set_cols_dtype("a,t,f4,i")` (decorative-comma string),
  `"atf4i"`, and `["f2","e4","i","I"]` all render exactly as before. The tokenizer is
  untouched, so this should hold trivially; pin it anyway to lock the guarantee.
- **New:** `F2` -> `123,456.79`; bare `F` uses global precision; `E` grouped scientific (if
  included); `F`/`f`/`I`/`i` produce the four distinct expected strings for the same value;
  grouped code + a callable column coexist; invalid tokens still raise the enumerating error.
- **Edge cases (required, from plan-review):**
  - Negative value: `F2` over `-1234.5` -> `-1,234.50` (sign preserved, grouped).
  - Non-numeric value: `F` over `"hello"` falls back to text (renders `hello`, no crash),
    matching the current `I`-over-text behavior.
  - Large value crossing multiple groups: `F0` over `1234567` -> `1,234,567`.
- **CLI:** `--dtype "tF2"` produces grouped decimals end-to-end.
- **Drift guard:** `test_dtype_help_enumeration_matches_format_map` still passes with `F`/`E`
  added to both `COLUMN_DTYPES` and `format_map`.
- Full `python -m pytest` green (currently 139).

## Docs / help sync

- README "Thousands separators with decimals, currency, and custom formats" subsection: add
  the `F` (and `E`) grouped code beside the callable recipes (callables still recommended for
  currency, which `F` does not cover).
- `docs/API.md` `set_cols_dtype`, `docs/CLI.md` `--dtype`: document the `F`/`E` codes.
- CHANGELOG: add an `Added` entry under a NEW `[1.3.0]` section. (1.2.0 is already published
  to PyPI at release time; a new additive public code is a minor bump, so this ships as 1.3.0,
  not by re-opening [Unreleased]. Bump `pyproject.toml` and `__version__` to 1.3.0 as part of
  execution, or explicitly defer the release to a later batch, do not ship the code under a
  1.2.0 label.)

## Non-goals

- No currency/locale subsystem, no bundled currency table, no locale detection. Currency is a
  literal the caller supplies (callable now; optional affix affordance only if chosen in review).
- No general Python format-spec passthrough in the token (rejected: collides with the tokenizer
  and is already covered by callables).

## Open questions

1. **Currency affordance:** ship grouped-float code ONLY (currency stays callable/documented),
   or also add a `set_cols_affix`/prefix-suffix later? Recommend code-only first; affix is a
   separate increment if demanded.
2. **Include `E` (grouped scientific)?** Cheap and symmetric, but low value. Recommend include
   for consistency; drop if it adds any noise to `_dtype_help()`.
3. **Comma overload:** RESOLVED by plan-review, do NOT overload the comma; use the `F` code.
   Confirm `F` (vs some other letter) reads best as "grouped float" alongside `I`.

## Approval and execution gate

Proposal only; not executed. Requires human approval (`Status: approved`) before execution.

Open questions that must be resolved by the human before or at execution:
- OQ1 currency affordance (recommend code-only; callables cover currency).
- OQ2 include `E` grouped scientific (recommend yes; trivial and symmetric).
- OQ3 confirm the letter `F` reads best for "grouped float" alongside `I`.

Execution steps on approval:
1. Pin characterization tests FIRST: existing dtype strings (`f2`, `e4`, `i`, `I`, `t`, `a`,
   and comma-decorated `"a,t,f4,i"` == `"atf4i"`) render byte-identically.
2. Add `F` (and `E` if approved) to `COLUMN_DTYPES` + `format_map` + new `_fmt_comma_float`
   /`_fmt_comma_exp`; the tokenizer and comma-strip are UNCHANGED.
3. Add the new + edge-case tests (negatives, non-numeric fallback, bare-`F` global precision,
   `F`/`f`/`I`/`i` distinctness, CLI `--dtype "tF2"`).
4. Sync README/API.md/CLI.md and add the CHANGELOG `[1.3.0]` entry; bump version to 1.3.0.
5. Run the full suite and paste the ACTUAL runner output into the execution record (do not
   claim a pass you did not run).

Scope fence: this plan changes ONLY numeric-grouping dtype support and its docs/tests. It does
NOT add currency/locale support, does NOT touch the tokenizer/comma-strip, and does NOT alter
any other formatter's output.

Commit and lifecycle: commit only the files changed by this work, path-scoped
(`git commit -- <paths>`), never `git add -A`, never push. On completion move this IPD from
`.agents/plans/pending/` to `.agents/plans/executed/` and set `Status: executed`.
