# Release Review 20260717-191234 - Final Report

Target: **vistab 1.2.1**. Focused review of the 1.2.1 delta (the `F`/`E` grouped-number dtype
codes, dtype help/docs, the version correction 1.3.0 -> 1.2.1, and the README Showcase section)
since the prior full review `20260711-181922`. All eight audit sections covered; depth
concentrated on the delta. Framework dirs and `workflow-artifacts/` excluded per protocol.

## 1. Completed actions

| ID | What | Validation |
|----|------|------------|
| (this run) | Verified the 1.2.1 delta across all eight sections; created run artifacts | see below |

No code/doc changes were needed this run: the 1.2.1 work was already built through an approved
IPD + two plan-reviews + tests + doc sync in prior commits. This review is a verification pass.

Validation evidence gathered:
- `pytest`: **146 passed**.
- `python -m build` + `twine check`: **PASSED** (sdist + wheel).
- Version **1.2.1** consistent across `pyproject.toml`, `__version__`, and `vistab --version`.
- Shipped `long_description`: **0 relative links, 25 v1.2.1-pinned URLs, no stray v1.2.0/v1.3.0, 5 Project-URLs**.
- New `F`/`E` formatters verified over 0, -0.0, 1e15, whitespace strings, ints, and non-numeric (text fallback), no crash.
- `F`/`E` documented consistently in README, API.md, CLI.md, CLI help (`_dtype_help`), and CHANGELOG `[1.2.1]`.

## 2. Identified but not addressed

| ID | What | RR + axis | Reason | Next step |
|----|------|-----------|--------|-----------|
| S6-2 | 1.2.1 is prepared but not tagged/pushed/published (no `v1.2.1` tag; `origin/main` behind local at `c959941` vs `f986c08`; PyPI at 1.2.0) | Low | Not a repo defect; it is the maintainer's Section 9 release action (remote/tag/upload), which requires explicit approval | On GO: create+push `v1.2.1` tag on the release commit so the pinned URLs resolve, push `main`, then `twine upload` |

No BLOCKER/HIGH/MEDIUM code, security, test, or docs findings. No `LIVE`/`MEM` findings (pure
formatting library, no I/O or state surface). LSP type-hint warnings in `src/vistab.py` are
pre-existing, runtime-harmless, and outside the 1.2.1 delta.

## 3. Fix Bar summary
Nothing to fix: the delta arrived pre-hardened. The single open item (S6-2) is a release-time
maintainer action, not a deferral of a defect.

## 4. Pending plans / staged prompts
None in scope. `.agents/plans/pending/` holds only its directory README; no pending prompts; no
status/location mismatches (fixed in the prior review). Pre-flight ask correctly skipped (clean).

## 5. TODO / backlog reconciliation
`TODO.md` is an honest future-roadmap (rowspan, jagged-row routing, CLI ideas), all marked
"Future Consideration"; Colspan correctly marked "Completed in v1.2.0". Nothing is mis-stated as
shipping in 1.2.1. No change needed.

## 6. Guiding principles (fallback set; no project principles file)
- Intuitive/self-documenting: `F` mirrors `I`; help enumerates AND explains every code. PASS.
- General-case/configurable: callable escape hatch covers currency/any format. PASS.
- KISS: no comma overload, no currency/locale subsystem, tokenizer untouched. PASS.
- Honest docs: limitations (currency needs a callable; CLI can't pass callables) are stated. PASS.

## 7. Eight-persona sign-off (delta)
QA/QC, tester: edge inputs + 146 green, drift-guard. UI/UX, novice: help explains codes; docs
have copy-paste recipes. Architect, engineer: additive, tokenizer-safe, single source of truth.
Power user: `F2` on CLI, callables for anything. Stakeholder: closes the "commas + decimals"
gap cleanly, correct semver. No persona surfaced a blocking concern.

## 8. Push / no-push
No push performed. The 1.2.1 commits are local (`origin/main` behind). Recommendation: on your
GO, push `main`, tag `v1.2.1` on the release commit, then upload to PyPI (uploads remain yours).

## 9. Restart
No restart recommended. Small, well-understood delta; verification clean.

---

## RELEASE REVIEW DECISION

**Recommendation: GO (CONDITIONAL) for vistab 1.2.1.**

The repository content for 1.2.1 is ready: tests green (146), build + twine PASS, version and
version-pinned docs consistent, docs coherent, no unfixed findings.

The one condition is a maintainer release action, not a code change:
- **S6-2**: create + push the `v1.2.1` tag on the release commit, push `main`, then
  `twine upload` (so the `/v1.2.1/` README URLs resolve and PyPI advances from 1.2.0).

AWAITING YOUR GO/NO-GO for Section 9 release execution. Nothing is pushed, tagged, or uploaded
until you explicitly say so, and PyPI uploads remain yours to run.
