# Implementation Plan - `show showcase` demo + README screenshot refresh

Status: PROPOSED (not yet executed)

> **Plan-review note (2026-07-11, revisions applied).** Claims verified against current
> code: `--demo` choices at `src/vistab.py:3652`, the `show`/`demo` dispatch tables at
> `3551`/`3581`, `vistab-demo-themes-01.png` present while `-02`/`vistab-M-themes-output.png`
> are absent (confirms the collapse and the broken CLI.md link), and `ocean-rows-index`
> exists. Findings R1-R5 folded in: the color-ON byte-identical + no-styling-escape pins the
> last release review established are now REQUIRED for the showcase demo (R2); the CLI.md
> broken image link is reclassified as a fix-now defect, not optional polish (R3); the "Likely
> OK" screenshot column is now grounded in the verified color-ON regression pin rather than
> asserted (R4); the showcase gets a concrete width target so the hero image is legible (R5);
> and the KISS/scope justification for a NEW demo subject is made explicit (R1).

Two related pieces of v1.2.0 docs/polish, bundled because the new demo produces the new
hero screenshot:

1. Add a curated **`vistab show showcase`** demo: one designed table that exercises the
   v1.2.0 headline capabilities together (colspan + a theme + ANSI/CJK content + wrapping),
   as the single "here's what vistab can do" flagship.
2. Refresh the **outdated README/CLI screenshots** (the screenshot PNGs predate this
   session's changes) and fix a **broken image link** in `docs/CLI.md`.

This does NOT block the v1.2.0 release (already tagged + GitHub-released; PyPI upload is the
maintainer's manual step). It is post-release docs polish.

## Prose convention

No em dashes in authored prose (repo/AGENTS.md convention); use periods, commas, colons,
or parentheses.

## User Review Required

> [!IMPORTANT]
> - The screenshot PNGs must be captured by the maintainer (a real terminal + screenshot
>   tool renders ANSI as an image). This IPD prepares everything around that: the demo to
>   capture, the exact commands, and the doc references. The agent does not fabricate PNGs.
> - No table rendering/API/CLI behavior changes beyond adding the `showcase` demo subject.

---

## Part 1: `vistab show showcase` demo

### Rationale (and scope justification, R1)
The existing demos are intentionally siloed to teach one capability each (`capabilities` =
wrapping, `themes` = theme grid, `span` = colspan, `anatomy` = coordinate styling). None
shows the v1.2.0 story in one glance. Rather than concatenate them (a long scroll), add a
single curated example: a realistic themed table with a spanned header, some colored/CJK
content, and wrapping, that reads well as one screenshot.

**KISS check (a new demo subject is net-new surface):** this is justified by a concrete,
stated driver, a v1.2.0 hero screenshot for the README top, not "combine everything." It is
one small function reusing existing machinery (no new abstraction, dependency, or engine
change). If, on review, an existing demo (e.g. a re-shot `show span`, which already renders
colspan + borders) serves as an acceptable hero, prefer that and DROP the new subject (see
Open Question 4). Do not add the subject if it does not earn its keep as the flagship.

### Change
- Add `def print_showcase_demo()` in `src/vistab.py` that renders ONE designed table:
  a theme applied (e.g. `ocean-rows-index`), a `ColSpan` header grouping, at least one
  wrapped multi-line cell, and a cell with ANSI-colored and/or CJK content, so it visibly
  demonstrates colspan + theme + color-aware wrapping at once. **(R5) Width target:** the
  table must fit within **80 columns** (set `max_width=80` or size columns accordingly) so
  the hero screenshot reads cleanly and does not horizontally scroll (the `show themes` grid
  is deliberately wide; the showcase must not repeat that). Verify the rendered visible width
  (ANSI-stripped) is <= 80.
- Wire it as a subject under BOTH the `show` and `demo` verbs' `valid_subjects`
  (`src/vistab.py:3551` show, `3581` demo) as `"showcase": print_showcase_demo`, and add it
  to the `--demo` argparse `choices`. Add subject-help lines for it in both verbs.
- **Honor `--no-color`/`NO_COLOR` (reuse the v1.2.0 seam):** build the table with
  `.set_color(_CLI_COLOR)`, route any literal-escape titles through `_demo_text(...)`, and
  call `_maybe_warn_color_off()` at the end (this is a color-centric demo). Content ANSI that
  is part of the demonstration may remain, matching the `capabilities` precedent, but then
  the warning must fire.
- Consider a short caption line naming the features shown ("colspan + theme + CJK/ANSI
  wrapping").

### Part-1 verification (R2: carry the same pins the CLI-polish release review established)
- `vistab show showcase`, `demo showcase`, `--demo showcase` all render (exit 0) and the
  output contains the spanned/themed/colored table.
- **`--no-color` pin:** stdout contains **no vistab-generated styling escapes** (the same
  assertion used for the other color demos). If the showcase intentionally embeds colored
  demonstration content (matching the `capabilities` precedent), that content may remain, but
  then `_maybe_warn_color_off()` MUST fire; a purely-chrome-colored showcase must be fully
  monochrome under `--no-color`. Pick one and test it explicitly. Do not ship a
  half-suppressed demo (this is exactly the B1/U1 gap the prior release review caught).
- **Color-ON stability:** adding the subject must not change any existing demo's or table's
  default (color-on) output; the release-review color-ON byte-identical pin still holds.
- **Width (R5):** assert the ANSI-stripped visible width of every showcase line is <= 80.
- Add CLI tests (`tests/test_cli.py`): `show showcase` exits 0 and renders the table;
  `show showcase --no-color` is escape-free on stdout (or warns, per the chosen policy).
- Full `python -m pytest` green.

---

## Part 2: Screenshot refresh + broken-link fix

### 2a. Fix the broken CLI.md image (a real DEFECT, fix now, not "polish") (R3)
`docs/CLI.md:118` references
`https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-M-themes-output.png`,
which **does not exist** in `docs/assets/` (verified) and is named after the removed `-M`
flag. A broken image renders as a broken-link icon on GitHub and PyPI, so this is a shipped
doc defect, not optional polish, and is **fix-by-default now** (Low remediation risk, pure
doc edit; does not depend on Part 1 or the maintainer's screenshot capture). Repoint it to
the existing `vistab-demo-themes-01.png` (or remove the image line). Also soften CLI.md:74
wording (the legacy `-M`/`-L`/`-C` flags are gone; `--demo` forms are the aliases).

### 2b. Re-capture stale screenshots (maintainer captures the PNGs)
Assessed against what changed this session:

| Asset | Status | Re-capture command |
|---|---|---|
| `vistab-demo-themes-01.png` | **Updated already by maintainer** (new borderless/unquoted output; themes-02 removed) | `vistab show themes` (done) |
| **NEW hero/showcase** | **Missing** (no single "what vistab does" image; v1.2.0 headline) | `vistab show showcase` (after Part 1) |
| `vistab-code-output-01.png` (Quick Start) | Likely OK (round-header quick-start unchanged) | re-shoot only if desired: the README Quick Start snippet |
| `vistab-demo-styles.png` | Likely OK (styles list unchanged) | `vistab show styles` |
| `vistab-demo-anatomy.png` | Likely OK (anatomy demo unchanged) | `vistab show anatomy` |
| `vistab-demo-colors.png` | Likely OK | `vistab show colors` |
| `vistab-demo-capabilities.png` | Likely OK | `vistab show capabilities` |
| `vistab-theme-ocean-rows-index-example*.png` | Likely OK | the two `vistab ~/test.csv --theme ...` commands in README |
| `vistab-CLI-basic.png`, `vistab-CLI-formatting.png` | Likely OK | the CLI.md example commands |

Only two are *known* stale/missing: the themes shot (already handled) and the new showcase
shot. The "Likely OK" rows are grounded, not asserted (R4): the release review verified the
default **color-ON** rendered output is byte-identical to the prior tip, and the CLI-polish
changes only altered demo *chrome*/`--no-color` paths, not the default screenshots' content.
Before declaring any "Likely OK" shot final, do a quick eyeball that the current command's
color-on output matches the existing PNG; re-shoot only on a real mismatch. Do not re-shoot
the 9 unchanged ones as a blocker.

### 2c. Add the hero image to the README top (after Part 1 ships the demo)
Once the showcase PNG exists, add it high in the README (near the top, above or beside the
Quick Start) as the flagship image, captioned as the colspan+theme+wrapping showcase, with
an **absolute** raw.githubusercontent URL (PyPI does not resolve relative image paths).
Cross-link `show span`/`show themes` sections to it.

### Part-2 verification
- No broken image links remain in `README.md`/`docs/CLI.md` (every referenced asset exists
  in `docs/assets/`).
- All image URLs are absolute `raw.githubusercontent.com/.../main/docs/assets/...` (PyPI-safe).
- Maintainer confirms the re-captured PNGs match current output.

---

## Non-goals
- No syntax-highlighter or new rendering behavior beyond the showcase demo.
- Not re-shooting screenshots whose output did not change (styles/anatomy/colors/etc.),
  unless the maintainer wants a consistent refresh.
- Agent does not generate image files.

## Open questions
1. **Subject name:** `showcase` vs `demo`/`everything`/`hero`? Recommend `showcase`
   (unambiguous, not colliding with the `demo` verb). Confirm.
2. **Showcase content:** which theme + what sample data best reads as a hero image? Propose
   `ocean-rows-index` + a small realistic table with a `ColSpan` header, one wrapped cell,
   and one CJK/ANSI cell; maintainer to approve the exact look before it becomes the README
   hero.
3. **Full re-shoot vs minimal:** re-capture only the 2 known-stale (themes done + new
   showcase), or refresh all 11 for visual consistency? Recommend minimal now; full refresh
   optional.
4. **Hero from an existing demo instead? (R1/KISS)** Before building `show showcase`,
   confirm a purpose-built showcase is wanted rather than promoting a re-shot existing demo
   (e.g. `show span`, which already renders colspan + borders) to hero. If an existing shot
   is acceptable, DROP Part 1 and keep only Part 2. Recommend the curated showcase (it tells
   the combined story better), but this is the maintainer's call.

## Approval and execution gate
Proposal only; not executed. Execution order on approval:
1. **Fix 2a now** (the broken CLI.md image link) regardless of the Part-1 decision, since it
   is a shipped doc defect independent of the screenshots.
2. If the showcase is approved (Open Q4): implement Part 1 (demo + tests, honoring the R2
   color pins and R5 width target); run verification.
3. Hand the capture list (2b) to the maintainer; wire the hero image (2c) once the PNG
   exists.
4. Run full verification; move this IPD to `.agents/plans/executed/`.
