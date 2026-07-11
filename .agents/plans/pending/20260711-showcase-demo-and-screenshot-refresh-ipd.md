# Implementation Plan - `show showcase` demo + README screenshot refresh

Status: PARTIALLY EXECUTED. Part 1 (`show showcase` demo) and Part 2a (broken CLI.md link)
are DONE and committed (`23b2a02`). Remaining: Part 2b (maintainer captures the showcase PNG)
and Part 2c (wire the hero image into the README). See "Execution status (2026-07-11)" below.

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

> **Plan-review note (2026-07-11, re-review after partial execution).** Re-verified against
> the current tree, which now already implements most of this plan:
> - **Part 1 DONE:** `print_showcase_demo()` exists at `src/vistab.py:3485`; wired into the
>   `show` dispatch (`src/vistab.py:3628`, help at `3639`), the `demo` dispatch
>   (`src/vistab.py:3660`, help at `3671`), and the `--demo` argparse `choices`
>   (`src/vistab.py:3729`). Three CLI tests cover it (`tests/test_cli.py:279` render,
>   `:291` width `<= 80`, `:342` `--no-color` fully monochrome + warns). Full suite 121 green.
> - **Part 2a DONE:** `docs/CLI.md:118` now points at the existing `vistab-demo-themes-01.png`;
>   verified every PNG referenced by `README.md`/`docs/CLI.md` exists in `docs/assets/` and
>   every image URL is an absolute `raw.githubusercontent.com/.../main/docs/assets/...`.
> - **Implementation deltas from the written spec (both benign, no defect):** the showcase uses
>   `max_width=72` (the plan's R5 said "80"; 72 is stricter and still satisfies `<= 80`), and
>   the `--no-color` policy chosen is "fully monochrome + warn" (the plan's R2 offered a choice;
>   this is the stronger option). The prose below is updated to match what shipped.
> - Findings this pass (all Low remediation risk, all fixed here): F1 stale "not executed"
>   status corrected; F2 stale `file:line` anchors refreshed; F3 width-target text reconciled to
>   72; F4 Open Questions 1 and 4 marked RESOLVED by the shipped decision; F5 Part 2c hardened
>   to re-verify the new asset exists (absolute URL, meaningful alt text) before committing the
>   README edit, so we do not reintroduce the broken-link class 2a just fixed.

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

## Execution status (2026-07-11)

| Part | Status | Evidence |
|---|---|---|
| 1. `show showcase` demo | **DONE** (`23b2a02`) | `print_showcase_demo()` at `src/vistab.py:3485`; wired at `:3628`/`:3660`/`:3729`; tests `tests/test_cli.py:279,291,342`; suite 121 green |
| 2a. Fix broken CLI.md image | **DONE** (`23b2a02`) | `docs/CLI.md:118` -> `vistab-demo-themes-01.png`; all referenced PNGs exist; all URLs absolute |
| 2b. Capture showcase PNG | **PENDING (maintainer)** | no `vistab-*showcase*.png` in `docs/assets/` yet |
| 2c. Wire hero image into README | **PENDING** | no showcase image reference in `README.md` yet; blocked on 2b |

Only 2b and 2c remain. The subsections below are retained for the historical record; the Part 1
and Part 2a subsections describe work that has already shipped (kept for auditability).

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
  table must fit within **80 columns** so the hero screenshot reads cleanly and does not
  horizontally scroll (the `show themes` grid is deliberately wide; the showcase must not
  repeat that). Verify the rendered visible width (ANSI-stripped) is <= 80. *(As shipped:
  `max_width=72`, which is comfortably within the 80 ceiling; the width test at
  `tests/test_cli.py:291` asserts `<= 80`.)*
- Wire it as a subject under BOTH the `show` and `demo` verbs' `valid_subjects` as
  `"showcase": print_showcase_demo`, and add it to the `--demo` argparse `choices`. Add
  subject-help lines for it in both verbs. *(As shipped: `show` dispatch at
  `src/vistab.py:3628` (help `:3639`), `demo` dispatch at `:3660` (help `:3671`), `--demo`
  `choices` at `:3729`. Earlier anchors 3551/3581/3652 predated the showcase code and are
  superseded.)*
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

### 2c. Add the hero image to the README top (REMAINING; after 2b delivers the PNG)
Once the showcase PNG exists, add it high in the README (near the top, above or beside the
Quick Start) as the flagship image, captioned as the colspan+theme+wrapping showcase, with
an **absolute** raw.githubusercontent URL (PyPI does not resolve relative image paths).
Cross-link `show span`/`show themes` sections to it.

**(F5) Guardrail so 2c does not reintroduce the broken-link defect 2a just fixed.** Before
committing the README edit:
- Decide and record the exact asset filename up front (recommend
  `docs/assets/vistab-demo-showcase.png` to match the `vistab-demo-*` convention) so the
  maintainer captures to that path.
- Verify the file actually exists in `docs/assets/` (do not write an `<img>`/`![]` line for a
  file that is not yet present; that is precisely the shipped broken-image class caught in 2a).
- Use an absolute `raw.githubusercontent.com/.../main/docs/assets/...` URL and meaningful,
  descriptive alt text (screen-reader accessible, per the honest-docs principle).
- Re-run the "every referenced PNG exists" check over `README.md`/`docs/CLI.md` after the edit.

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
1. **Subject name:** RESOLVED. Shipped as `showcase` (unambiguous, no collision with the
   `demo` verb), wired into both verbs and `--demo` choices.
2. **Showcase content:** which theme + what sample data best reads as a hero image? Propose
   `ocean-rows-index` + a small realistic table with a `ColSpan` header, one wrapped cell,
   and one CJK/ANSI cell; maintainer to approve the exact look before it becomes the README
   hero.
3. **Full re-shoot vs minimal:** re-capture only the 2 known-stale (themes done + new
   showcase), or refresh all 11 for visual consistency? Recommend minimal now; full refresh
   optional.
4. **Hero from an existing demo instead? (R1/KISS)** RESOLVED. The curated `show showcase`
   was built and shipped (one small function reusing existing machinery, no new abstraction),
   as it tells the combined colspan + theme + CJK/ANSI + wrapping story in one image. Part 1
   was kept, not dropped.

## Approval and execution gate
Partially executed (see "Execution status"). Done: Part 1 and Part 2a (`23b2a02`, tests green).
Remaining steps:
1. **2b (maintainer):** capture the showcase PNG from `vistab show showcase` to
   `docs/assets/vistab-demo-showcase.png` (the agent does not fabricate PNGs).
2. **2c (agent, after 2b):** wire the hero image into the README top with an absolute URL and
   meaningful alt text, honoring the F5 guardrail (verify the file exists first, then re-run
   the referenced-PNG existence check). Cross-link the `show span`/`show themes` sections.
3. Optionally (Open Q3) re-shoot the "Likely OK" screenshots if the maintainer wants a
   consistent refresh; not a blocker.
4. Run full verification; when 2c lands, move this IPD to `.agents/plans/executed/`.

This IPD stays in `pending/` until 2b + 2c complete (it is not fully executed yet).
