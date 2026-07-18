# Plan Review Changes — Colspan Support IPD

**Reviewed file:** `.agents/plans/pending/20260709-colspan-support.md`
**Reviewer role:** pre-execution plan reviewer (plan-review workflow)
**Verdict:** APPROVE WITH REVISIONS APPLIED
**Audience:** Gemini (the agent that will execute the plan)

This document explains *what* I changed in the IPD and *why*. I did not touch any
application code, tests, or configuration — only the planning document. Every edit was
a planning-doc edit (low remediation risk), so per the Fix Bar I fixed by default rather
than deferring.

---

## How I reviewed

I read the actual source in `src/vistab.py` and verified each of the plan's claims
against the real methods (`set_header`, `add_row`, `_check_row_size`,
`_compute_cols_width`, `_len_cell`, `_str`, `_draw_line`, `_splitit`, `_apply_sorting`,
`_infer_auto_dtypes`, `_check_align`, `_get_active_ansi_wrap`). I also ran the test
suite: 66 pass, 6 pre-existing failures in `tests/test_regression.py` (CLI/theme/edge)
that are **unrelated** to this plan — do not treat them as caused by colspan work, but
be aware they exist before you start.

No `GUIDING_PRINCIPLES.md`/`PRINCIPLES.md` exists in the repo, so I applied the
universal fallback principles (intuitive/self-documenting, general-case/configurable,
KISS, honest docs) plus the `FUNCTIONAL_SPEC.md` invariant that additions "must preserve
backward compatibility."

---

## The core problem the original draft missed

The plan migrates cells from plain strings to `VistabCell` objects, but the *existing*
engine assumes strings in many hot paths the plan did **not** rewrite. As soon as a cell
becomes an object, those paths crash or corrupt output. Most of my edits make that
migration safe.

---

## Findings and the edits I applied

| ID | Severity | Finding | Edit made |
|----|----------|---------|-----------|
| F1 | BLOCKER | `set_header` does `list(map(obj2unicode, ...))` (src/vistab.py:1772), which stringifies `ColSpan`/`VistabCell` and permanently destroys header span metadata — header spans (Case 1) could never work. | Added a BLOCKER-fix callout in **§3.2** requiring that line be replaced with `self._header = self._expand_spans_in_row(processed_array)` so headers hold objects, symmetric with data rows. |
| F2 | BLOCKER | `_len_cell` (2256) and the base loop in `_compute_cols_width` (2307) call `cell.split('\n')`; `_infer_auto_dtypes`/`_check_align` call `str(row[c])`. These break on `VistabCell`. | Added the **mandatory `VistabCell.__str__`** requirement in **§3.1** (returns `str(self.value)`, `""` for placeholders) making cells string-transparent, and updated **§3.5** to compute base widths via `str(cell)`. |
| F3 | BLOCKER | `_apply_sorting` sorts rows in place using `str(row[col_idx])` (1148). With objects the key breaks, and span/placeholder adjacency was unaddressed. | Added new **§3.4b** describing the sort key (safe via `__str__`) and proving column-span atomicity (rows move whole, so source+placeholders stay adjacent). Added a regression assertion requirement and a note that future row-spans must re-block rows before sorting. |
| F4 | BLOCKER | `_draw_line` zips `line, self._width, self._align`; `_splitit` zips `line, self._width`. The new colspan loops advance by `colspan` and can't use those 1:1 zips. Outer `range(self.vislen(line[0]))` assumes equal line-counts per column. | Added **§5.1** requiring explicit indexing of the physical-length lists, span-width combination from the source column, alignment from the source cell, and padding placeholder `[]` line-lists to the row's max line-count to avoid `IndexError`. |
| F5 | BLOCKER (sec) | `_draw_line` sanitizes destructive ANSI per physical column (2534-2539); the span path must not skip this or it reopens the terminal-hijack vector (`sanitize_ansi`, SPEC §12). | Added **§5.2** requiring identical ANSI sanitization on the merged span content. |
| F6 | MEDIUM | Alternating styling uses `col_idx % 2` (1341); span rendering shifts parity and leaves covered-column styling undefined. | Added **§5.3**: span block adopts the **source** column's style; placeholder columns contribute no independent style. |
| F7 | MEDIUM | Ambiguity: §3.2 converts to objects at ingestion, §3.6 re-wraps at draw time — two sources of truth. | Added **§3.1a** establishing ingestion-time objects as canonical, and clarifying that `_str` formats `value` in place and copies metadata (revising §3.6 intent) so nothing is lost. |
| F8 | MEDIUM | Span width added to `self._width[j]`, but `_max_width` redistribution (2320-2340) reshrinks without span knowledge, risking negative `fill`/overflow. | Added **§5.4**: run span distribution after the `_max_width` shrink, or feed span minimums into the shrink, or clip via existing `on_wrap_conflict`. |
| F9 | MEDIUM | New public API (`ColSpan`, `set_header_span`, `set_cell_span`) not synced to `FUNCTIONAL_SPEC.md`; contract requires it. | Added **§5.5**: update `FUNCTIONAL_SPEC.md`, `docs/API.md`, and `CHANGELOG.md` as part of "done." |
| F10 | LOW | Test item numbering could drift ("Test 4.1-item-4" = Sorting). | Added **§5.6** clarifying the reference; kept list order. |

---

## Structural edits (where to look in the revised plan)

- **Header note (top):** a "Plan-review note (revisions applied)" block summarizing
  principles used and sections changed.
- **§3.1:** added the mandatory `VistabCell.__str__` string-transparency requirement
  (load-bearing — do not skip).
- **§3.1a (new):** single source of truth — cells become objects at ingestion; draw-time
  `_str` formats in place and copies span metadata.
- **§3.2:** BLOCKER-fix callout to replace the `obj2unicode` map in `set_header`.
- **§3.4b (new):** sorting interaction and column-span atomicity.
- **§3.5:** base width now uses `str(cell)`; source/placeholder cells contribute 0 to a
  single physical column's base width.
- **§5 (new): Open Questions & Cross-Cutting Constraints** — §5.1 parallel lists, §5.2
  ANSI sanitization, §5.3 zebra parity, §5.4 `_max_width` vs span minimum, §5.5 spec
  sync, §5.6 test numbering.

---

## What I intentionally did NOT change

- I did not rewrite the §3.6–3.9 pseudocode line-by-line; the constraints in §5.1–5.4
  tell you what those sections must additionally satisfy. Implement to the constraints.
- I did not fix the 6 pre-existing `test_regression.py` failures — out of scope for this
  plan and not caused by it.
- No deferrals: there are no findings left unaddressed on Medium-High+ remediation-risk
  grounds. Everything above is either fixed inline or specified as a required constraint.

---

## Bottom line for the implementer

The plan is sound in approach (object grid + sentinel placeholders). The riskiest part is
the string→object migration: **implement `VistabCell.__str__` first**, fix `set_header`'s
`obj2unicode`, and honor the §5 cross-cutting constraints (especially §5.1 indexing and
§5.2 ANSI sanitization) or the render path will crash or emit unsafe output. Sync the
spec/docs/changelog before marking the milestone done.

---

# Second review pass — hardening for a fast implementer

This pass was done specifically knowing the implementer (Gemini) is fast but tends to
skim nuance and under-address architecture. The goal here was less about finding *new*
crash bugs and more about **structuring the plan so a careless implementation is hard and
a clean one is the path of least resistance.** Read `.agents/plans/pending/20260709-colspan-support.md`
§0 first — it is the acceptance gate.

## New findings from pass 2

| ID | Severity | Finding | Edit made |
|----|----------|---------|-----------|
| F11 | BLOCKER | The original plan never mentioned `_build_hline` (src/vistab.py:2219). It joins **every** physical column boundary with a junction glyph (`┬ ┼ ┴`), so a colspan gets a junction poking into the middle of the merged block — visibly broken boxes. §4.2 claimed to verify box alignment but nothing achieved it. | Added **§3.9a** specifying junction suppression at boundaries interior to a span (row-context-aware, or a documented whole-table superset), plus a required box-drawing test (§4.1 item 7). |
| F12 | HIGH (correctness) | The §3.5 width-distribution used `deficit/(k+1)` with float division. `k+1` is wrong (a k-column span covers k columns, not k+1), and float division causes rounding drift → off-by-one border misalignment. | Rewrote §3.5 to distribute over **k** columns using integer `divmod`, so covered widths sum back exactly to the target. |
| F13 | ARCH (drift-prevention) | Span width + separator math was going to be hand-coded independently in §3.5, §3.8, §3.9, and (missing) §3.9a. A fast implementer will copy-paste it slightly differently in each, and the borders/wrapping/widths will silently disagree. | Added **§3.0**: one `_sep_width()` + one `_span_block_width()` helper that ALL four sites must call. Made "no copy-pasted geometry" a Definition-of-Done item. This is the single highest-leverage change for a clean result. |

## Structural hardening (not bugs, but guardrails)

- **§0 Implementer Contract** — the skim-proof front matter:
  - **§0.1** names the one rule (centralized geometry) that prevents most bugs.
  - **§0.2** a mandatory step order where each step must leave the existing suite green;
    step 2 (ingestion) is called out as *the* regression checkpoint — if plain-value
    tables break there, stop before adding span behavior.
  - **§0.3** a checkbox **Definition of Done** with 8 non-negotiable invariants
    (backward-compat golden output, rectangularity, adjacency, geometry agreement, no
    junction artifacts, ANSI safety, no copy-pasted geometry, docs synced). Each requires
    a test/assertion.
  - **§0.4** a **scope fence / "Do NOT touch"** list, so the implementer fixes span code
    rather than mutating public signatures, ANSI routines, the `_max_width` algorithm, or
    pre-existing expected outputs — and does not "fix" the 6 unrelated pre-existing
    regression failures to make the bar look green.
- **§4 tests rewritten to be assertive.** The old list said things like "renders
  correctly" / "formats without collapsing" — a half-correct implementation passes those.
  Each test now states the exact string/invariant to assert (centered field width, absence
  of interior vertical rule, `divmod` sum exactness, adjacency before/after sort, no
  junction glyphs interior to a span). Added the **backward-compat golden test** (item 6)
  and **box-drawing integrity test** (item 7) as Definition-of-Done gates.

## Why this shape helps a fast/sloppy implementer specifically

1. **Centralization over discipline.** Instead of trusting the implementer to compute the
   same geometry consistently in four places, there is now one function to call.
   Consistency becomes structural, not a matter of care.
2. **A single visible acceptance gate.** §0.3 is a checklist; even a skimming agent that
   ignores the prose can run down eight checkboxes. Backward-compat is a golden-output
   test, so "I didn't break anything" is mechanically verifiable, not asserted.
3. **Ordered, green-at-each-step build.** §0.2 makes the risky migration (strings→objects)
   its own checkpoint, so a regression is caught at the moment it is introduced rather
   than after six interacting changes.
4. **Tests that fail on sloppiness.** Exact-output assertions turn "looks fine" into a
   red bar when geometry is off by one — the errors this feature is most prone to.
5. **A scope fence.** The "Do NOT touch" list heads off the classic sloppy move of
   editing shared/public code or pre-existing test expectations to make spans "work."

## Verdict after pass 2

**APPROVE WITH REVISIONS APPLIED.** Approach unchanged and sound; the additions make the
correct implementation the easy one and give clear, mechanical acceptance criteria. No
deferrals. Start at §0, build §3.0 first, keep the suite green at every step in §0.2.
