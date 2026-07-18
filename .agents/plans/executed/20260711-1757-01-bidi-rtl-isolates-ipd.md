# Implementation Plan - Bidi-safe rendering: LTR-isolate each cell so RTL content does not flip the table grid

Status: EXECUTED (2026-07-11). Implemented `set_bidi()` + `--no-bidi` + `_contains_rtl`/`_RTL_RE`
+ table-level gate (draw and stream paths) + zero-width isolate injection at the `_draw_line`
seam. 14 new tests (bidi core, --no-bidi CLI, width-neutral + non-RTL byte-identical pins,
mixed cell, and multi-color word-wrap boundary pins); suite 121 -> 135 green. The capabilities
demo fixture was regenerated because that demo already contains Arabic/Hebrew: verified the
isolate-stripped fixture is byte-identical to the prior one (proves the change is purely
additive isolates, no layout change). Docs synced (API.md set_color/set_bidi, CLI.md --no-bidi,
README RTL note + hero image), CHANGELOG updated. Empirically confirmed in mintty: raw RTL rows
flip the grid; isolate-wrapped rows keep the grid stable with correct intra-cell RTL.

When a cell contains right-to-left (RTL) script (Arabic, Hebrew, etc.), the terminal runs the
Unicode Bidirectional Algorithm (UAX #9) over the whole physical output line. A strong RTL
character makes the terminal reorder the entire line: the `│`-delimited cells reverse order and
the row becomes right-aligned, so the table grid visibly breaks (confirmed live in mintty on
the showcase demo, rows 5 and 6). vistab's width and padding math is correct; the terminal
reorders the finished bytes at display time.

## Prose convention

No em dashes in authored prose (repo/AGENTS.md convention); use periods, commas, colons, or
parentheses.

## Reproduction (verified in mintty)

`vistab show showcase` rows 5 (Arabic) and 6 (Hebrew) render right-aligned with reversed cell
order, while all LTR rows render normally. Empirically tested three variants of the real
showcase table written to files and viewed in a bare mintty (outside any TUI):

- **A (raw, no marks):** grid broken (rows flip, right-aligned). This is the bug.
- **B (each cell content wrapped in U+2066 LEFT-TO-RIGHT ISOLATE .. U+2069 POP DIRECTIONAL
  ISOLATE):** grid stable AND the Arabic/Hebrew still reads correctly RTL inside the cell
  (e.g. `(Ada)` sits on the right). This is the chosen fix.
- **C (single U+200E LRM prefixed per line):** also stabilizes the grid (kept as documented
  fallback, not implemented).
- **D (mixed Arabic + Latin + digits in one isolated cell):** resolves correctly inside stable
  borders.

Maintainer confirmed A breaks and B is correct.

## Chosen approach: per-cell LTR isolates (Unicode UAX #9)

Wrap each cell's finalized content in `U+2066 (LRI) .. U+2069 (PDI)`. This tells the terminal
"treat this cell as a self-contained bidi island: resolve direction inside it, but do not let
it reorder anything outside it." Consequences:

- The table grid (borders, cell order, column alignment) stays LTR and stable, because every
  inter-border content segment is an isolated LTR island, so the line's base direction is
  unambiguously LTR.
- Inside each cell, the terminal still runs full bidi, so RTL text reads right-to-left and
  mixed content (Arabic + Latin + numbers) orders naturally. We do NOT flatten intra-cell
  direction (that is why isolates are correct and a blunt whole-line LTR force is not).
- Isolates are zero-width: verified `wcswidth('\u2066')==0`, `wcswidth('\u2069')==0`, and
  `wcswidth('\u2066Ada\u2069')==wcswidth('Ada')`. So column width math is unaffected.

## Design decisions (resolved with maintainer)

1. **Wrap every cell unconditionally (when the feature is active), not "only mixed cells."**
   The trigger for the terminal's flip is "the line contains ANY strong RTL char," not "a cell
   is internally mixed," so a per-cell "is it mixed" test is both wrong (a pure-RTL cell still
   flips the row) and slower (a full range scan of every cell) than just wrapping. Wrapping a
   pure-LTR cell in an LTR isolate is a visual and width no-op. Consistent wrapping is what
   makes the grid provably stable.
2. **Gate at the table level for performance.** Do a single cached pass over all cell content
   when rendering: if NO cell contains an RTL codepoint, do nothing at all (zero cost and
   byte-identical output for the overwhelmingly common ASCII/CJK-only tables). Only when RTL
   is present (and bidi is enabled) do we wrap cells. This is the right perf seam: one pass,
   not per-cell conditionals, and skipped entirely for non-RTL tables.
3. **Mixed cells need no special handling.** The isolate gives each cell its own bidi context;
   the terminal orders the mixed runs correctly within it. This is the point of using isolates.
4. **Scope = cell content only**, not every string vistab prints. Titles/captions/the demo
   code block are author-controlled single strings and are left alone.

## Proposed change (`src/vistab.py`)

- **RTL detection helper.** Add a module-level `_HAS_RTL` compiled regex covering the strong-RTL
  Unicode blocks (Hebrew `U+0590-05FF`, Arabic `U+0600-06FF`, Arabic Supplement `U+0750-077F`,
  Arabic Extended-A `U+08A0-08FF`, Arabic Presentation Forms-A `U+FB50-FDFF` and Forms-B
  `U+FE70-FEFF`, Syriac `U+0700-074F`, Thaana `U+0780-07BF`, plus RTL-mark scalars). A small
  `_contains_rtl(text: str) -> bool`.
- **`Vistab._bidi` flag, default True**, with `set_bidi(self, enabled: bool = True) -> "Vistab"`
  (chainable, matching `set_color`). Docstring states what it does and that some terminals
  ignore isolates (graceful degradation: no worse than off).
- **Cached table-level gate.** In the draw entry point, compute once per draw whether any cell
  (header + rows) contains RTL; store on a transient attribute (e.g. `self._bidi_active =
  self._bidi and any(...)`). Reset/recompute each `draw()` so mutation between draws is honest.
- **Inject at the render seam.** In `_draw_line` (`src/vistab.py:2993`), immediately after
  `cell_line` is finalized and BEFORE `fill = w - self.vislen(cell_line)` (line 2998), if
  `self._bidi_active`, set `cell_line = "\u2066" + cell_line + "\u2069"`. Because `vislen`
  treats the isolates as zero-width, `fill` is unchanged and all alignment/padding math is
  identical. Padding stays OUTSIDE the isolate (it is appended around `cell_line` at
  3013-3022), which is correct: the fill spaces must not be pulled into the RTL run.
  - Verify interaction with ANSI reassert/sanitize (2994-2996) and clip (`_ansi_safe_clip`):
    inject the isolates AFTER clipping/reassert so we never clip an isolate off and leave an
    unbalanced LRI without its PDI.
- **CLI:** add `--no-bidi` (and honor nothing env-side unless we later want a `VISTAB_NO_BIDI`).
  Wire it in `main()` to `set_bidi(False)` on the table, mirroring `--no-color`. Add a
  module-level `_CLI_BIDI` if the demos need it, consistent with `_CLI_COLOR`.

## Invariants and anti-regression

- **Non-RTL tables must be byte-identical to today** (color-on and `--no-color`). The
  table-level gate guarantees this: no RTL means no code path change. Pin with a
  characterization test on an existing table.
- **Width/geometry unchanged even when isolates are injected** (zero-width). Pin: the visible
  width (ANSI + isolate stripped) of an RTL table equals the width computed without bidi.
- **`--no-color` still fully monochrome**; isolates are not ANSI and are orthogonal, but assert
  both can combine (RTL + `--no-color`) with no styling escapes and isolates present.
- **Balanced isolates:** every injected LRI has a matching PDI; clipping happens before
  injection so a clip can never orphan one.

## Verification

- **New tests (`tests/test_vistab.py` and/or `tests/test_cli.py`):**
  - `_contains_rtl`: true for Arabic/Hebrew samples, false for ASCII/CJK/accented Latin.
  - RTL cell → rendered output contains `\u2066`/`\u2069` around that cell's content; a
    pure-ASCII table contains neither.
  - **Width neutrality:** for an RTL table, stripping ANSI and the isolate chars yields the
    same per-line visible width as the same data with `set_bidi(False)`.
  - **Byte-identical pin:** an existing non-RTL table renders identically with the feature
    present (proves the gate is a true no-op for the common case).
  - `set_bidi(False)` / `--no-bidi`: no isolates in output even with RTL content.
  - Mixed cell (Arabic + Latin + digits): isolates wrap the whole cell content exactly once
    (balanced), width matches the non-bidi computation.
  - Showcase rows 5 and 6: assert the Arabic/Hebrew cell content is isolate-wrapped so the grid
    stays stable (structural assertion; we cannot assert terminal display, but we can assert
    the marks are present and balanced and width is unchanged).
- Full `python -m pytest` green (currently 121).

## Spec / documentation sync

- `docs/API.md`: document `set_bidi()`.
- `docs/CLI.md`: document `--no-bidi`.
- `README`: a short "Right-to-left (Arabic/Hebrew) text" note explaining vistab isolates each
  cell so RTL content does not flip the grid, that intra-cell RTL still reads correctly, and
  that a few terminals ignore isolates (use `--no-bidi` / `set_bidi(False)` if needed).
- `CHANGELOG.md` `[Unreleased]` Added: "Bidi-safe rendering: RTL (Arabic/Hebrew) cells are
  wrapped in Unicode LTR isolates so they no longer flip the table grid; toggle with
  `set_bidi()` / `--no-bidi`."
- `FUNCTIONAL_SPEC` if it enumerates rendering guarantees.

## Non-goals

- Not implementing full shaping/joining or a bundled bidi engine; we rely on the terminal's
  UAX #9 (the correct layer). No new runtime dependency.
- Not changing intra-cell reading order (isolates deliberately preserve it).
- Not attempting to fix terminals that ignore isolates beyond offering `--no-bidi` and
  documenting the C (per-line LRM) fallback for future consideration.

## Open questions

1. **Default on vs off.** Recommend ON by default: the common case (no RTL) is a zero-cost
   no-op, and users with RTL data get correct grids without opting in. `--no-bidi` /
   `set_bidi(False)` is the escape hatch for the rare isolate-ignoring terminal. Confirm.
2. **Env var.** Add `VISTAB_NO_BIDI` alongside `--no-bidi` for parity with `NO_COLOR`, or keep
   it flag/API only for now? Recommend flag + API only initially (smaller surface); add env if
   requested.
3. **RTL block coverage.** The regex covers the major strong-RTL blocks; confirm we do not also
   want to trigger on RTL override/embedding control chars themselves (recommend detecting the
   script blocks, not the control chars).

## Approval and execution gate

Proposal only; not executed. On approval: implement the detection + gate + injection +
`set_bidi()`/`--no-bidi`, add the tests (including the non-RTL byte-identical pin and the
width-neutrality pin), sync docs/CHANGELOG, run full verification, and move this IPD to
`.agents/plans/executed/`.
