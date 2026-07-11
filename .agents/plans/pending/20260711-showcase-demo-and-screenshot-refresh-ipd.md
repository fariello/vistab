# Implementation Plan - `show showcase` demo + README screenshot refresh

Status: PROPOSED (not yet executed)

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

### Rationale
The existing demos are intentionally siloed to teach one capability each (`capabilities` =
wrapping, `themes` = theme grid, `span` = colspan, `anatomy` = coordinate styling). None
shows the v1.2.0 story in one glance. Rather than concatenate them (a long scroll), add a
single curated example: a realistic themed table with a spanned header, some colored/CJK
content, and wrapping, that reads well as one screenshot.

### Change
- Add `def print_showcase_demo()` in `src/vistab.py` that renders ONE designed table:
  a theme applied (e.g. `ocean-rows-index`), a `ColSpan` header grouping, at least one
  wrapped multi-line cell, and a cell with ANSI-colored and/or CJK content, so it visibly
  demonstrates colspan + theme + color-aware wrapping at once. Keep it compact (fits a
  normal terminal width, good as a hero image).
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

### Part-1 verification
- `vistab show showcase`, `demo showcase`, `--demo showcase` all render (exit 0) and the
  output contains the spanned/themed/colored table.
- `--no-color`: chrome is monochrome and the color-off WARNING fires; color-ON output is
  stable.
- Add a CLI test (in `tests/test_cli.py`) asserting `show showcase` renders and exits 0.
- Full `python -m pytest` green.

---

## Part 2: Screenshot refresh + broken-link fix

### 2a. Fix the broken CLI.md image (real dead link, do now / low risk)
`docs/CLI.md:118` references
`https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-M-themes-output.png`,
which **does not exist** in `docs/assets/` and is named after the removed `-M` flag. Repoint
it to the existing (updated) `vistab-demo-themes-01.png`, or remove the image line. Also
soften CLI.md:74 wording (the legacy `-M`/`-L`/`-C` flags are gone; `--demo` are the aliases).

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
shot. The rest are old but their rendered output did not change this release; re-shoot them
opportunistically, not as a blocker.

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

## Approval and execution gate
Proposal only; not executed. On approval: implement Part 1 (showcase demo + tests), fix the
CLI.md broken link (2a), then hand the capture list (2b) to the maintainer; wire the hero
image (2c) once the PNG exists; run verification; move this IPD to `.agents/plans/executed/`.
