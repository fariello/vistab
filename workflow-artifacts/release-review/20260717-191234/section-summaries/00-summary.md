# Section summaries - release-review 20260717-191234 (target: vistab 1.2.1)

Scope: focused review of the 1.2.1 delta (F/E grouped-number dtype codes + dtype help/docs +
version correction 1.3.0->1.2.1 + README Showcase section) since the prior full review
20260711-181922. All eight sections covered; depth on the delta. Auto-parallel not engaged
(single small delta, serial is cheaper).

## S1 current-state
HEAD f986c08 on main, clean tree. Pre-flight glance: pending/ holds only its dir README (not a
plan), no pending prompts, no status/location mismatches, 0 code TODO/FIXME. TODO.md is an
honest future-roadmap (rowspan etc., all "Future Consideration"). No blocking signal, so the
pre-flight ask was correctly skipped. Considered-not-done: full re-audit of pre-1.2.1 code
(covered by the prior review; only the delta is new).

## S2 quality/security/edge-cases
New formatters _fmt_comma_float/_fmt_comma_exp verified across 0, -0.0, 1e15, whitespace-padded
numeric strings, ints, and non-numeric (FallbackToText). No crash; outputs are standard Python
format-spec results. Tokenizer UNCHANGED (F/E are new letters), so no injection/parse-surface
change. No security surface (pure formatting lib). LSP type-hint warnings are pre-existing,
runtime-harmless, and out of the 1.2.1 delta. No findings.

## S3 tests/regression
Full suite 146 passed. 1.2.1 added dtype tests (grouping, negatives, non-numeric fallback,
bare-F global precision, f/F/i/I distinctness, existing-strings-unchanged) + a drift-guard
(COLUMN_DTYPES == format_map keys). Regression fixtures regenerated for the grown help text and
verified additive-only (isolate/help text) in prior commits. No findings.

## S4 docs/specs/examples
F/E documented consistently in README (Showcase + number-formatting recipes), docs/API.md,
docs/CLI.md, the CLI --help/error via the single-source _dtype_help(), and CHANGELOG [1.2.1].
Currency correctly documented as a callable (no locale guessing). No findings.

## S5 feature/usability/maintainability + principles + TODO
Principles (fallback set): intuitive (F mirrors I; help enumerates+explains), general-case
(callable escape hatch), KISS (no comma overload, no currency subsystem, tokenizer untouched),
honest docs (limitations stated). TODO.md reconciled: honest, nothing mis-stated as shipped in
1.2.1; roadmap items are explicitly future. No findings.

## S6 compatibility/packaging/release
version 1.2.1 consistent (pyproject, __version__, --version); build + twine check PASS;
long_description has 0 relative links, 25 v1.2.1-pinned URLs, no stray 1.2.0/1.3.0, 5
Project-URLs. Semver correct: additive patch over published 1.2.0. Release-state: no v1.2.1
tag, origin/main behind local, PyPI at 1.2.0 -> the tag/push/upload is the maintainer's
Section 9 step (S6-2), not a repo defect.
