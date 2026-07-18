# IPD: Subject/verb/object CLI subcommands (`show`, `help`, `demo`)

- Date: 2026-07-10
- Concern: ui-ux / CLI design (with docs sync)
- Scope: `src/vistab.py` `main()` CLI dispatch only (plus the theme-demo padding fix and a new `span` demo); docs sync in `docs/CLI.md`, `README.md`, `FUNCTIONAL_SPEC.md`, `CHANGELOG.md`. No library/rendering-engine changes except the two demo-content tweaks.
- Status: EXECUTED (show/help/demo verbs shipped in 1.2.0). Status corrected 2026-07-11 during release-review 20260711-181922 (stale PENDING line on an executed/-located plan).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> **Updates incorporated (2026-07-10).** Three refinements from
> `20260710-cli-verb-commands.updates.md` (now in `executed/`) were folded in as findings
> U1-U3: (U1) regenerate `regression_diagnostic_matrix.txt` with the theme-demo padding
> change or `test_demo_themes` breaks (Step 5); (U2) `--demo` accepts the same aliases as
> the `demo` verb, resolved via the shared alias table (Step 6); (U3) guard
> `len(sys.argv) > 1` in the pre-parse dispatch so a bare `vistab`/empty-STDIN does not
> `IndexError` (Step 2 + Design). All three verified against the current code before
> incorporation; U2 was adopted per intent but implemented via the shared normalizer rather
> than bloating argparse `choices` (see Step 6 rationale).

> **Plan-review note (2026-07-10).** Re-verified against current HEAD. Disambiguation is
> sound (verified: `./show`, `-i show`, `--help`, bare `vistab`, and `data.csv` all fall
> through correctly; only a bare first-token `show`/`help`/`demo` dispatches as a verb).
> Findings R1-R3 added: **R1 (HIGH)** — the `help` verb cannot use the same pure pre-parse
> dispatch as `show`/`demo`, because `--help-colors`/`--help-advanced` output is produced by
> `parser.print_help()` *after* verbosity `SUPPRESS` lambdas are set from `sys.argv`
> (vistab.py:3368-3374, 3447-3448); `help` must instead translate to injecting the matching
> `--help-*` token and letting normal flow render. R2/R3 are test-home and coverage
> refinements.

## Goal

Give the CLI intuitive, natural-language **subject/verb/object commands** (e.g.
`vistab show styles`) as the primary, discoverable way to run the diagnostic/help/demo
operations that today are hidden behind flags (`vistab --demo styles`,
`vistab --help-colors`). The flag forms remain as **backward-compatible aliases** (they are
documented and shipped, and the `--show-code` regression fixture depends on flag parsing).
Also: add a `demo span` that shows column spanning (and later row spanning) with printed
example code, and shrink the over-wide `demo themes` output by rendering the inner sample
tables with `padding=0`.

The maintainer's target grammar (canonical examples):

```
vistab show styles          == vistab --demo styles
vistab show colors          == vistab --demo colors
vistab show capabilities    == vistab show caps      == vistab --demo capabilities
vistab show anatomy         == vistab --demo anatomy
vistab show themes          == vistab --demo themes
vistab show <unknown>       -> help for `vistab show` (list valid subjects), non-zero exit
vistab help colors          == vistab --help-colors
vistab demo span            == vistab --demo span    -> comprehensive colspan/rowspan demo + example code
vistab demo rowspan         == vistab demo colspan   -> (until rowspan ships, both map to the span demo)
```

## Project conventions discovered (Step 0)

- **Stack / entry point:** single-module lib+CLI; console script `vistab = "vistab:main"`
  ([pyproject.toml:29](file:///home/gfariello/VC/vistab/pyproject.toml)). CLI is `argparse`
  in `main()` ([src/vistab.py:3323](file:///home/gfariello/VC/vistab/src/vistab.py)),
  `add_help=False`, custom `usage_str`.
- **Guiding principles:** no `GUIDING_PRINCIPLES.md`; universal fallback — intuitive/
  self-documenting, KISS, honest docs, **no silent failure** (an unknown subject must show
  help, not do nothing or crash).
- **Current diagnostic surface (all flags today):**
  - `--demo {styles,colors,capabilities,anatomy,themes}` ([src/vistab.py:3380](file:///home/gfariello/VC/vistab/src/vistab.py)),
    dispatched at [src/vistab.py:3520-3543](file:///home/gfariello/VC/vistab/src/vistab.py).
  - `--help-colors`, `--help-advanced` ([src/vistab.py:3381-3382](file:///home/gfariello/VC/vistab/src/vistab.py)),
    which set help-verbosity flags and reprint help ([src/vistab.py:3447-3449](file:///home/gfariello/VC/vistab/src/vistab.py)).
  - Demo renderers: `print_styles_list` (3166), `print_colors_list` (3231),
    `print_themes_demo` (3286), `print_test_demo` (3122 = capabilities),
    `print_coordinate_styles_demo` (3186 = anatomy).
- **Plan lifecycle:** `.agents/plans/{pending,executed,reusable}/`, `YYYYMMDD-<slug>.md`.
- **Test/docs coupling:** `docs/CLI.md` already documents `--demo ...` (dead `-M/-L/-C` were
  removed in the executed documentation IPD). A `--show-code` gold-master fixture depends on
  flag parsing (do not break flags). `FUNCTIONAL_SPEC.md` §5 describes CLI patterns.
- **Domain invariant:** positional `files ...` (`nargs="*"`,
  [src/vistab.py:3393](file:///home/gfariello/VC/vistab/src/vistab.py)) currently consumes
  bare positionals. The new verbs are also positionals, so the parser must disambiguate a
  **subcommand** (`show`/`help`/`demo` as the first positional) from **file paths** without
  breaking `vistab data.csv` or `cat x | vistab`.

## Design (subject/verb/object grammar)

### Verbs and subjects

| Verb | Subjects | Maps to |
|------|----------|---------|
| `show` | `styles`, `colors`, `capabilities`(alias `caps`), `anatomy`, `themes` | the existing `--demo <subject>` renderers |
| `help` | `colors`, `advanced`(alias `adv`), (bare `help` → general help) | `--help-colors` / `--help-advanced` / `--help` |
| `demo` | `span`(aliases `colspan`, `rowspan`), plus **all `show` subjects** as synonyms | new span demo; other subjects reuse the `show` renderers |

Notes:
- `show` and `demo` overlap intentionally: `demo` is the natural word for "run a
  demonstration," and `show` for "show me the X." Both accept the visual subjects; only
  `demo` additionally accepts `span`. (Keeping one canonical set of subject→renderer
  mappings, shared by both verbs — see KISS below.)
- **Alias table** (subject synonyms, case-insensitive): `caps`→`capabilities`,
  `adv`→`advanced`, `colspan`/`rowspan`→`span`. Until row spanning ships, `rowspan` maps to
  the same span demo and the demo notes rowspan is "coming soon."

### Unknown-subject behavior (no silent failure)
`vistab show <unknown>` (or `demo`/`help` with an unknown subject) prints a concise usage
block for that verb — the list of valid subjects with one-line descriptions — to **stderr**
and exits **non-zero (2)**, matching argparse's convention for a usage error. A **bare**
verb (`vistab show` with no subject) does the same (shows the verb's help) but exits **0**
(it's a help request, not an error). This split keeps scripts honest (typos fail) while a
bare verb is a friendly menu.

### Parser integration (how to disambiguate verbs from files) — KISS
Do **not** restructure the whole parser into argparse subparsers (that would fragment the
~60 shared flags across subparsers and risk regressions in the `--show-code`/theme paths —
high Complexity/Functionality remediation risk). Instead:

1. Add a light **pre-parse dispatch** at the very top of `main()` (before
   `parser.parse_args()`): **guard the length first** — only inspect the first positional
   when `len(sys.argv) > 1`; a bare `vistab` (no args) must fall straight through to the
   normal STDIN-reading path (today `vistab` with no args reads STDIN and exits 0, and
   `cat x | vistab` is a primary use case, so an unguarded `sys.argv[1]` would raise
   `IndexError` and break both). If the first token is one of the reserved verbs
   `{show, help, demo}`, route to a dedicated `handle_verb(verb, rest)` function that
   resolves the subject (with aliases) and dispatches:
   - **`show` / `demo`** call the standalone module-level renderers (`print_styles_list`,
     `print_colors_list`, `print_test_demo`, `print_coordinate_styles_demo`,
     `print_themes_demo`, and the new `print_span_demo`) directly and `sys.exit()`. These
     take no `args`, so they never need the flag parser — file parsing and all flags are
     untouched.
   - **`help` (R1 — cannot use a standalone renderer):** the help output for
     `--help-colors`/`--help-advanced` is produced by `parser.print_help()` *after* the
     verbosity `SUPPRESS` lambdas (`b_help`/`a_help`/`c_help`) are set from `sys.argv`
     ([src/vistab.py:3368-3374](file:///home/gfariello/VC/vistab/src/vistab.py),
     [src/vistab.py:3447-3449](file:///home/gfariello/VC/vistab/src/vistab.py)). A pre-parse
     handler that exits before the parser is built cannot reproduce this. Therefore the
     `help` verb must **translate to the equivalent flag and continue through normal flow**:
     rewrite `sys.argv` so `help colors` → `--help-colors`, `help advanced`/`help adv` →
     `--help-advanced`, and bare `help` → `--help`, then fall through to the normal
     `parser`/`parse_args()` path (do NOT early-exit for `help`). This reuses the existing,
     tested help-rendering path verbatim (single source of truth) instead of duplicating it.
2. Reserved-verb collision guard: if a user genuinely has a file literally named `show`,
   `help`, or `demo`, they can still render it via `vistab ./show` or `-i show` (document
   this). The bare word is treated as a verb. This is the standard Git-style tradeoff and
   is acceptable given these are natural command words.
3. The existing flags (`--demo`, `--help-colors`, `--help-advanced`) remain fully
   functional and are the alias/back-compat path; the verb dispatch and the flags call the
   **same** underlying renderer functions (single source of truth).

### Theme-demo width fix
In `print_themes_demo` ([src/vistab.py:3286-3321](file:///home/gfariello/VC/vistab/src/vistab.py)),
the **inner** sample tables are built with default `padding=1`, making the six-column grid
of nested tables too wide. Render each inner `Vistab(tdata).set_theme(...)` with
`padding=0` (the outer demo table already uses `padding=0`). This is content-only; it does
not change the theme definitions themselves.

### New `span` demo
Add `print_span_demo()` that renders a reasonably comprehensive colspan demonstration
(inline `ColSpan`, coordinate `set_cell_span`/`set_header_span`, `combine` merging, and the
directional-junction rendering) **and prints the example code** that produced it (mirroring
the `examples/colspan_demo.py` content). It must note that row spanning is not yet
implemented and that `rowspan`/`colspan` currently both show the colspan demo. Reuse
`examples/colspan_demo.py` as the source of truth where practical to avoid drift.

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate. (C* = original review;
U* = incorporated 2026-07-10 from `20260710-cli-verb-commands.updates.md`.)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| C1 | Medium | Low | Novice | Discoverability | Diagnostic/demo operations are only reachable via non-obvious flags (`--demo`, `--help-colors`); a natural `vistab show styles` does not work. | [src/vistab.py:3380-3382](file:///home/gfariello/VC/vistab/src/vistab.py) |
| U1 | High | Low | Testing/regression | Fixture coupling | The Step 5 theme-demo padding change alters `--demo themes` stdout, which is pinned by `test_demo_themes` against `regression_diagnostic_matrix.txt`; without regenerating the fixture the suite fails. Folded into Step 5. | [tests/test_demo.py:89-92](file:///home/gfariello/VC/vistab/tests/test_demo.py); fixture `tests/fixtures/regression_diagnostic_matrix.txt` |
| U2 | Low | Low | Power user | Flag/verb parity | For consistency the `--demo` flag should accept the same aliases (`caps`, `colspan`, `rowspan`) as the `demo` verb, resolved via the shared alias table. Folded into Step 6. | [src/vistab.py:3380](file:///home/gfariello/VC/vistab/src/vistab.py) |
| U3 | Medium | Low | QA | Crash on no-arg invocation | An unguarded `sys.argv[1]` in the pre-parse dispatch would `IndexError` for a bare `vistab` / empty STDIN (a primary use case). Requires a `len(sys.argv) > 1` guard. Folded into Step 2 + Design. | [src/vistab.py:3323](file:///home/gfariello/VC/vistab/src/vistab.py) `main()` |
| R1 | High | Low | Architect / SWE | `help` verb parser coupling | (Plan-review.) `--help-colors`/`--help-advanced` render via `parser.print_help()` after verbosity `SUPPRESS` lambdas are set from `sys.argv`; a pre-parse standalone handler can't reproduce that. The `help` verb must translate to injecting the matching `--help-*`/`--help` flag and fall through to normal flow, not early-exit. Fixed in Design + Step 2. | [src/vistab.py:3368-3374](file:///home/gfariello/VC/vistab/src/vistab.py), [src/vistab.py:3447-3449](file:///home/gfariello/VC/vistab/src/vistab.py) |
| R2 | Medium | Low | Testing | Test home | (Plan-review.) The verb-equivalence tests belong in `tests/test_demo.py`, which already has the `_run_cli`/`_assert_against_fixture` harness and the `--demo`/`--help` counterparts — not a vaguely-named "CLI test module". Fixed in Required tests. | [tests/test_demo.py:19-92](file:///home/gfariello/VC/vistab/tests/test_demo.py) |
| R3 | Low | Low | QA | `show`/`demo` overlap untested | (Plan-review.) Open Q1 lets both verbs accept visual subjects, but nothing asserts e.g. `demo styles` works. Added to test matrix. | this IPD Open Q1 |
| C2 | Medium | Low | Novice | No span demo | There is no `demo span`; the shipped colspan feature has no CLI demonstration despite `examples/colspan_demo.py` existing. | demo choices [src/vistab.py:3380](file:///home/gfariello/VC/vistab/src/vistab.py) |
| C3 | Low | Low | Novice / stakeholder | Over-wide theme demo | `demo themes` renders inner sample tables at `padding=1`, producing an excessively wide grid. | [src/vistab.py:3286-3321](file:///home/gfariello/VC/vistab/src/vistab.py) |
| C4 | Low | Low | Novice | Stale error tips | Error tips still say "Run 'vistab -L'"/"'vistab -M'" — flags that no longer exist (should be `vistab show styles` / `vistab show themes`). | [src/vistab.py:3457](file:///home/gfariello/VC/vistab/src/vistab.py), [src/vistab.py:3463](file:///home/gfariello/VC/vistab/src/vistab.py) |
| C5 | Low | Low | Novice | Usage string | The `usage_str` and `--demo` help advertise only the flag form; should also show the verb form. | [src/vistab.py:3346-3353](file:///home/gfariello/VC/vistab/src/vistab.py) |

## Proposed changes (ordered, validatable)

Fix by default; all Low Remediation Risk (additive dispatch + content tweaks; no engine
changes; flags preserved).

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | C1 | Add a single source-of-truth mapping `subject -> renderer` (`styles`→`print_styles_list`, `colors`→`print_colors_list`, `capabilities`→`print_test_demo`, `anatomy`→`print_coordinate_styles_demo`, `themes`→`print_themes_demo`) and a subject-alias table (`caps`→`capabilities`, `adv`→`advanced`, `colspan`/`rowspan`→`span`). | `src/vistab.py` | Low | Unit test: mapping resolves each canonical subject + alias. |
| 2 | C1, R1 | Add `handle_verb(verb, args_rest)` and a pre-parse dispatch at the top of `main()`: **guard `len(sys.argv) > 1`** (so a bare `vistab` / empty STDIN does not `IndexError`), then if the first positional token is exactly `show`/`help`/`demo`, resolve subject via the alias table. **`show`/`demo`** invoke the standalone renderer and `sys.exit`. **`help` (R1) does NOT early-exit** — it rewrites `sys.argv` to the equivalent `--help-*`/`--help` flag and falls through to the normal `parse_args()`/`print_help()` path, so the filtered-help behavior is reused, not duplicated. | `src/vistab.py` | Low | `show styles/colors/caps/anatomy/themes` match their `--demo` equivalents; **`help colors`≡`--help-colors`, `help advanced`≡`--help-advanced`, bare `help`≡`--help`** (byte-compare stdout). `vistab` no-args and `printf '' \| vistab` exit cleanly (no `IndexError`); `vistab data.csv`, `cat x \| vistab`, `vistab --help`, `vistab ./show`, `vistab -i show` all behave as before (no regression). |
| 3 | C1 | Unknown-subject + bare-verb behavior: unknown subject → verb-specific usage to **stderr**, exit **2**; bare verb → same usage to **stdout**, exit **0**. Never silently no-op. | `src/vistab.py` | Low | `vistab show bogus` exits 2 with a subject list on stderr; `vistab show` exits 0 with the same list on stdout. |
| 4 | C2 | Add `print_span_demo()` (comprehensive colspan demo + printed example code; notes rowspan is not yet implemented) and wire `demo span`/`demo colspan`/`demo rowspan` (and `--demo span` as the flag alias) to it. Prefer sourcing content from `examples/colspan_demo.py` to avoid drift. | `src/vistab.py` | Low | `vistab demo span`, `demo colspan`, `demo rowspan`, and `--demo span` all render a colspan table and print example code; output is non-empty and crash-free. |
| 5 | C3, U1 | In `print_themes_demo`, build each inner sample table with `padding=0`. **This changes the `--demo themes` stdout, which is pinned by `test_demo_themes` against `tests/fixtures/regression_diagnostic_matrix.txt` ([tests/test_demo.py:89-92](file:///home/gfariello/VC/vistab/tests/test_demo.py)). Regenerate that fixture in the SAME change** (after manually confirming the narrower output is correct), or `test_demo_themes` will fail. | `src/vistab.py`, `tests/fixtures/regression_diagnostic_matrix.txt` | Low | `vistab show themes` output is materially narrower (assert max line width below a threshold); `test_demo_themes` passes against the regenerated fixture; theme *definitions* unchanged. |
| 6 | C1, U2 | Add `"span"` to the `--demo` argparse `choices`. **For full flag/verb parity (U2):** the `--demo` flag must accept the *same aliases* as the `demo` verb (`caps`, `colspan`, `rowspan`). Implement this by normalizing the value through the **shared subject-alias table (Step 1)** rather than listing raw aliases in argparse `choices` — i.e. accept the aliases but resolve them to canonical renderers via the one normalizer used everywhere. (Rationale: keeping argparse `choices` to the canonical set + `span` avoids advertising `caps`/`colspan`/`rowspan` as first-class values in auto-generated help while still giving 100% parity. If `type=`-based normalization is awkward, widening `choices` to include the aliases is an acceptable fallback — but resolution must still go through the single shared table, never a second copy.) | `src/vistab.py` | Low | `vistab --demo span`, `--demo caps`, `--demo colspan`, `--demo rowspan` all work and match their verb-form output; `--demo bogus` still rejected; alias resolution shares one table with the verb path (no divergence). |
| 7 | C4, C5 | Update error tips (`-L`→`show styles`, `-M`→`show themes`) and `usage_str`/`--demo` help to advertise the verb forms as primary with flags as aliases. | `src/vistab.py` | Low | Error tips reference working commands; `vistab --help` shows the verb grammar. |
| 8 | C1-C5 | Docs sync: `docs/CLI.md` (document the `show`/`help`/`demo` grammar, subjects, aliases, unknown-subject behavior, reserved-word/file caveat), `README.md` (use `vistab show styles` etc. in examples), `FUNCTIONAL_SPEC.md` §5 (CLI patterns), `CHANGELOG.md` `[Unreleased]` (new subcommands; flags retained as aliases). | `docs/CLI.md`, `README.md`, `FUNCTIONAL_SPEC.md`, `CHANGELOG.md` | Low | Every command shown in docs runs without error; reviewer confirms flags still documented as aliases. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| Full argparse subparser migration | Medium-High | complexity + functionality | Splitting the ~60 shared flags into per-verb subparsers risks regressions across the `--show-code`, theme, and streaming paths and adds maintenance burden for no user benefit over the lightweight pre-parse dispatch. Deferred; the pre-parse approach (Steps 1-3) delivers the grammar safely. | Revisit only if the verb surface grows large enough to need per-verb flags. |
| Row spanning demo content | Medium | functionality | Row spanning is not implemented; a real rowspan demo cannot exist yet. `rowspan` aliases to the colspan demo with a "coming soon" note now. | Add real rowspan demo when the rowspan feature ships. |

## Scope check

- **Over-scope:** none. The verb grammar is additive; flags are retained (no forced
  migration). Explicitly NOT converting *table-formatting* flags (`--width`, `--style`,
  `--theme`, colors, etc.) into verbs — only the **logical/diagnostic** operations
  (`show`/`help`/`demo`) per the request; turning formatting options into a verb grammar
  would be a large, low-value redesign (Complexity axis).
- **Under-scope:** the request's `demo span` needs a demo that does not yet exist (Step 4)
  and the theme-demo width fix (Step 5); both added.

## Required tests / validation

- **New CLI tests in `tests/test_demo.py` (R2)** — reuse its existing `_run_cli` /
  `_assert_against_fixture` harness, which already exercises the `--demo`/`--help`
  counterparts. For each verb command, assert output equals its flag equivalent —
  `show styles`≡`--demo styles`, `show caps`≡`--demo capabilities`≡`--demo caps`,
  `help colors`≡`--help-colors`, `help advanced`≡`--help-advanced`, bare `help`≡`--help`.
- **`show`/`demo` overlap (R3):** `demo styles`/`demo colors`/`demo themes` (etc.) render the
  same output as `show styles`/... — confirm both verbs accept the visual subjects.
- **Unknown/bare subject:** `show bogus` → exit 2 + subject list on stderr; `show` → exit 0
  + list on stdout.
- **Span demo:** `demo span`/`colspan`/`rowspan`/`--demo span` all succeed and print code.
- **Flag/verb alias parity (U2):** `--demo caps`≡`--demo capabilities`≡`show caps`;
  `--demo colspan`/`--demo rowspan`≡`demo span`. Alias resolution shares one table with the
  verb path.
- **No-arg / empty-STDIN safety (U3):** `vistab` (no args) and `printf '' | vistab` exit
  cleanly with no `IndexError`.
- **Fixture regeneration (U1):** `test_demo_themes` passes against the regenerated
  `regression_diagnostic_matrix.txt`.
- **No regression to data rendering:** `vistab <file>` and STDIN piping unaffected; the
  `--show-code` gold-master and existing CLI regression tests stay green.
- **Theme width:** assert `show themes` output is narrower than the current baseline.
- Full `python -m pytest` green.

## Spec / documentation sync

Covered by Step 8. Behavior is user-visible (new commands), so `docs/CLI.md`, `README.md`,
`FUNCTIONAL_SPEC.md` §5, and `CHANGELOG.md` must all reflect the verb grammar and that flag
forms are retained aliases.

## Open questions

1. **`show` vs `demo` overlap:** the plan lets both accept the visual subjects (with only
   `demo` adding `span`). Acceptable, or should `show` be reserved for "lists/palettes"
   (styles/colors/themes) and `demo` for "animated/example" renders (capabilities/anatomy/
   span)? (Assumption: both accept all visual subjects for forgiveness; confirm.)
2. **Reserved words vs. files named `show`/`help`/`demo`:** the pre-parse dispatch treats a
   bare first-positional `show`/`help`/`demo` as a verb. Confirm the documented escape
   (`vistab ./show` or `-i show`) is acceptable, or reserve the verbs only when **no** other
   file args/flags are present (more permissive but more surprising).
3. **`help advanced` subject word:** use `advanced` (alias `adv`) to mirror `--help-advanced`?
   (Assumed yes.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it) and answer the Open Questions.
2. On approval, execute Steps 1-8 in order, run the validation, and sync docs/spec.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
