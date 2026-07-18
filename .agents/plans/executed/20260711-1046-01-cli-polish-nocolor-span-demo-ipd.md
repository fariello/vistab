# Implementation Plan - CLI polish: library-first messaging, show/demo span, color control, span-demo redesign

Status: EXECUTED (--no-color, show/demo span, span-demo redesign shipped in 1.2.0). Status corrected 2026-07-11 during release-review 20260711-181922 (stale PROPOSED line on an executed/-located plan).

> **Plan-review note (2026-07-11, revisions applied).** Traced the actual ANSI-emission
> sites. Table *styling* ANSI is centralized (`_get_active_ansi_wrap` at
> `src/vistab.py:1497-1498`, `_get_border_ansi` at `1504-1505`), so a `_color_enabled` gate
> there is sound for tables. **But two gaps were found and fixed in the plan:** (R1) the
> color demos emit ANSI as *cell content and titles* (e.g. `print_colors_list` swatches at
> `src/vistab.py:3271`, titles at `3276/3293/3308`), which bypass the styling helpers, so
> `--no-color` must also govern demo/title/content color or the demos will still print color
> (and item 6's warning would lie); (R2) the "no `\033[` at all" verification is wrong
> because reset codes and *user-supplied* content ANSI legitimately remain, so the
> regression pin was reframed. R3/R4 tighten the color-ON pin and the highlight rule.

Grew out of a hands-on CLI session. Five related improvements to the CLI/demo surface,
plus one genuinely new small feature (`--no-color` / `NO_COLOR`) that a later item depends
on. No table *rendering* semantics change.

## Prose convention

No em dashes in authored prose (repo/AGENTS.md convention); use periods, commas, colons,
or parentheses.

## User Review Required

> [!IMPORTANT]
> - Public API additions only (a `Vistab` color toggle + a CLI flag). No change to table
>   geometry, alignment, spanning, or existing default output *when color is on* (the
>   default). Existing tests must stay green.
> - `--no-color` is a real new feature (vistab has no color-suppression today); it must be
>   table-wide, not a demo-only hack.

---

## Items

### 1. No-data / usage message hammers "use it as a library" (usability, `U`)

**Current state (verified):** running `vistab` with no data prints, via
`parser.print_usage()` + `src/vistab.py:3766-3768`:
`[ERROR] No tabular dataset found...` then a `--help` tip. The `usage_str`
(`src/vistab.py:3527`) has no library framing.

**Change:**
- Prepend a library-first line to the `usage_str` header so it appears on every usage/help
  print. Suggested (short):
  > `vistab can be used on the command line, but is intended primarily as a Python library:`
  > `    from vistab import Vistab`
- In the no-data error block (`src/vistab.py:3765-3769`), make the FIRST printed line the
  library nudge, then the existing error + tip:
  > `vistab is primarily a Python library; the CLI is for ad-hoc use. In code: from vistab import Vistab`

Keep it concise; do not bury the actual error.

### 2. `show span` / `show spans` should work, not just `demo span` (usability bug, `U`)

**Current state (verified):** the span demo (`print_span_demo`) is wired ONLY under the
`demo` verb (`src/vistab.py:3494-3495`); `show`'s `valid_subjects`
(`src/vistab.py:3463-3469`) has no `span`. So `vistab show span` errors while
`vistab demo span` works. That asymmetry is the trap the user hit.

**Change:**
- Add `"span": print_span_demo` to the `show` verb's `valid_subjects` (both verbs already
  share the visual subjects; this closes the gap).
- Add `"spans": "span"` to the `alias_map` (`src/vistab.py:3435-3440`) so `show spans` /
  `demo spans` also work. **Canonical stays `span`** (singular, matching `ColSpan`,
  `set_cell_span`, and a future `rowspan`); `spans`/`colspan`/`rowspan` are aliases.
- Add `span` to both verbs' usage/subject lists and to the `--demo` `choices`
  (`src/vistab.py:3564`) if not already resolvable (it already accepts span/colspan/rowspan).
- Update `usage_str`: `vistab show span` (not `demo span`) as the advertised form, since
  `show` is the primary verb.

### 3. Clearer wording for `capabilities` vs `anatomy` (usability, `U`)

**Current state:** `capabilities` -> `print_test_demo` (ANSI/CJK wrap + parse/format
conformance); `anatomy` -> `print_coordinate_styles_demo` (labeled parts of a table +
coordinate styling). Both read as "show me what vistab does," which is confusing.

**Change (low-touch, alias-based so nothing breaks):**
- **Keep `anatomy`** (it accurately means "the parts of a table"); no rename.
- For `capabilities`, add **`wrapping`** as an alias (its headline demonstration is
  ANSI/CJK-safe wrapping), and sharpen the one-line subject descriptions so the two are
  clearly distinct, e.g.:
  - `capabilities` (alias `caps`, `wrapping`): "ANSI + CJK-safe word-wrapping and datatype
    parsing conformance."
  - `anatomy`: "a labeled diagram of a table's parts (borders, header, cells) and
    coordinate styling."
- Do not remove `capabilities`/`caps`; they stay valid.

### 4. `--no-color` / `NO_COLOR` support (new feature, table-wide) (`F`)

**Current state (verified):** vistab has NO color-suppression. ANSI is emitted directly in
`_get_active_ansi_wrap`, `_get_border_ansi`, and style compilation; there is no central
toggle and no `--no-color` flag or `NO_COLOR` handling.

**Change (design for a real, testable seam):**
- Add a `Vistab` instance flag, e.g. `self._color_enabled` (default `True`), with a public
  setter/property (e.g. `set_color(enabled: bool)` / `color_enabled`).
- Gate ANSI emission on it at the **central** points: the ANSI-wrap and border-ANSI
  helpers (`_get_active_ansi_wrap` `src/vistab.py:1497-1498`, `_get_border_ansi`
  `1504-1505`) return empty on/off pairs when `_color_enabled` is False.
- **(R1) Content/demo/title ANSI is NOT covered by those helpers.** The color demos build
  ANSI directly into cell content and titles (e.g. `print_colors_list` swatches
  `f"\033[{val}m Sample \033[0m"` at `src/vistab.py:3271`; `set_title("\033[1;36m...")` at
  `3276/3293/3308`; demo section titles throughout). A gate on the styling helpers alone
  will still print those colors. So the CLI color-off path must ALSO make the color demos
  render without their hardcoded escapes: the cleanest approach is a module-level
  "color emitting allowed?" check the demos consult before embedding raw escapes (or route
  demo swatches/titles through the same suppression). Whatever the mechanism, the invariant
  is: **when color is off, no vistab-generated styling escape reaches stdout, including from
  demos and titles.** (User-supplied content ANSI is out of scope; see R2.)
- CLI: add `--no-color`; also honor the `NO_COLOR` env var (any non-empty value) and
  default to no color when stdout is not a TTY *only if that does not regress current piped
  behavior* (see Open Question 1 - piping currently emits color; changing that is a
  behavior change and must be a deliberate decision, not a silent one).
- Expose a way for the CLI layer to know color was suppressed AND which trigger fired
  (`--no-color` / `NO_COLOR` / non-TTY), so item 6 can print an honest warning.
- This is the dependency for items 5 and 6.

### 5. Span demo redesign: code immediately below each table + highlight span calls (`U`)

**Current state (verified):** `print_span_demo` (`src/vistab.py:3318-3367`) prints all
three demo tables first, then dumps all example code at the bottom.

**Change:**
- Interleave: for each of the 3 examples, print a short heading, the rendered table, then
  **its** example code directly beneath it (not all code at the end).
- Lightly colorize the example code, **highlighting only the span-specific tokens**
  (`ColSpan`, `set_cell_span`, `set_header_span`, `combine=`) so the eye lands on the point
  of the demo. **(R4) Concrete rule:** literal substring replacement of that fixed token
  list, wrapping each in one style code then reset (e.g. bold or bright color), applied to
  the code strings before printing. NO tokenizer, NO Python parser, NO general syntax
  highlighting (over-scope, Complexity axis). The token list is small and fixed.
- **Respect item 4:** all code colorization is suppressed when color is off (`--no-color`,
  `NO_COLOR`, or the chosen non-TTY rule). When suppressed, print plain code.

### 6. Color demos warn when color is suppressed (usability, no-silent-failure) (`U`)

**Rationale:** the color-centric demos (`show colors`, `show themes`, `show anatomy`, and
the span-demo's highlighted code) lose their entire point when color is off. Rendering them
monochrome with no explanation is a silent, confusing result.

**Change:** when a color-dependent demo runs while color is suppressed (via `--no-color`,
`NO_COLOR`, or the chosen non-TTY rule from item 4), print a trailing line at the **bottom**
of that demo's output:

> `WARNING: colors turned off by --no-color` (or `by NO_COLOR` / `(non-TTY output)` as
> appropriate to the actual cause, so the message is honest about which trigger fired).

Scope: applies to the demos whose value is color (`colors`, `themes`, `anatomy`, and the
span-demo code highlighting). It need not fire for purely structural demos (`styles`,
`capabilities`) unless those also emit color; decide per-demo by whether the renderer would
have emitted ANSI. The warning goes to stderr if the demo output is being captured, else
stdout at the end (keep it visible but out of the primary payload). Suppress the warning
itself from being colorized (it is a plain notice).

---

## Non-goals

- No change to table geometry, alignment, wrapping, spanning, or default colored output.
- No general/IDE syntax highlighter (only span-token emphasis in the span demo).
- No rename that removes `capabilities`/`caps`/`anatomy` (aliases only; back-compatible).
- Rowspan is still not implemented; `rowspan` remains an alias to the colspan demo.

---

## Verification

- `python -m pytest` stays green.
- **New tests:**
  - `vistab show span`, `show spans`, `demo span`, `demo spans` all render the span demo
    (exit 0); output identical across the aliases.
  - `capabilities`/`caps`/`wrapping` resolve to the same renderer; `anatomy` unchanged.
  - **Color toggle (R2, corrected):** for a table built with vistab styles/themes but
    **plain-string content**, a color-disabled render adds **no vistab styling escapes** and
    is byte-identical to the same table built with no styles applied. Do NOT assert "zero
    `\033[` anywhere": reset codes and any *user-supplied* content ANSI legitimately remain;
    the pin is "vistab emits no styling color," not "the output contains no escape bytes."
  - **Color ON regression pin (R3):** capture the rendered output of a representative themed
    table BEFORE item 4, assert it is byte-identical AFTER (item 4 edits the central ANSI
    helpers, which is exactly where a default-output regression would hide).
  - CLI `--no-color` and `NO_COLOR=1`: a themed render, and `show colors`/`show themes`,
    produce output with no vistab-generated styling escapes (including demo swatches/titles,
    per R1).
  - Span demo: with color on, span tokens are highlighted; with `--no-color`, the demo code
    contains no escape sequences.
  - Suppression warning (item 6): `vistab show colors --no-color` (and `themes`, `anatomy`,
    `show span --no-color`) ends with a `WARNING: colors turned off ...` line naming the
    actual trigger; the warning itself contains no escape sequences; a color-on run does
    NOT print the warning; purely structural demos do not emit a spurious warning.
- **Manual:** run `vistab` (no args) and confirm the library line is the first, clear
  message; run `vistab show span` and confirm each code block sits under its table.
- Update `docs/CLI.md` (show/demo subjects incl. span/spans/wrapping, `--no-color`),
  `README.md` if it lists subjects, and `CHANGELOG.md` `[Unreleased]`
  (`--no-color`/`NO_COLOR` is user-visible new behavior).

---

## Open questions

1. **Non-TTY default:** vistab currently emits ANSI even when piped. Should `--no-color`
   be *explicit-only*, or should color also auto-off when stdout is not a TTY (and honor
   `NO_COLOR`)? Auto-off on non-TTY is the common convention but is a **behavior change** to
   piped output that could surprise existing users capturing colored output. Recommend:
   honor `NO_COLOR` + explicit `--no-color` now; treat non-TTY auto-off as a separate,
   clearly-changelogged decision. Confirm.
2. **Public setter name:** `set_color(False)` vs a `color_enabled` property vs constructor
   kwarg `color=`? Recommend a `set_color(enabled=True)` fluent method for API consistency
   with the other `set_*` methods, plus reading `NO_COLOR` only at the CLI layer (keep the
   library env-agnostic). Confirm.

---

## Approval and execution gate

Proposal only; not executed. On approval, implement items 1-6 in order (item 4 before items
5 and 6, since both depend on the color-suppression seam), run the verification, sync docs,
and move this IPD to `.agents/plans/executed/`.
