# Persona Review (append per section)
## Section 1 (discovery)
- Stakeholder: project is coherent and near-releasable; the main stakeholder-visible gap is the unbumped version vs. the substantial unreleased feature set (S1-BUG1).
- Software engineer: single large module but well-tested (101 tests); type hints are loose (S1-Q1).

## Section 2 (quality/security/edge)
- QA/QC: happy + error paths covered; CLI errors are self-documenting (helpful tips on format error, vistab.py:4031). No broken-behavior finding.
- Software engineer: clean resource hygiene (all `with`-managed opens; bounded lru_cache); no eval/exec/pickle/subprocess; dtype Callable runs a user-supplied function, not eval of strings. Only smell: loose type hints (S1-Q1).
- Security-minded architect: attack surface is minimal (no auth/network/secrets); the one security feature (sanitize_ansi) strips destructive cursor sequences and is tested. No new finding.
- (Novice/stakeholder incidental): the `--sort-by`+`--stream` error message correctly explains the memory tradeoff rather than silently OOMing.

## Section 3 (tests/regression)
- Testing/regression expert: strong suite (101 tests, gold-master fixtures for demo/CLI/colspan/ANSI). Recent changes well-pinned (has_header 5 tests, junction glyphs 7 tests, combine options, CLI verbs 21 tests). Gaps: colspan width-distribution (T1), styling parity (T2), max_cols/stream/multi-span (T3) — Low severity, working-but-unpinned.
- QA/QC: the 6 previously-failing deprecation-warning regression tests are now green (apply_theme leak fixed). No brittle/misleading tests observed; fixtures are byte-exact which is appropriately strict for a renderer.

## Section 4 (docs/specs/examples)
- Complete novice: README opens with a clear one-line intent + Key Features + Quick Start; `pip install vistab` and `vistab[cjk]` documented; can reach first success from README alone. CLI diagnostics reachable via intuitive `vistab show styles`. No manual-required basic task found.
- UI/UX: docs and CLI terminology consistent (show/help/demo verbs mirror flags); API.md version-agnostic (no drift). Minor: architecture/decision rationale not in an obvious project-owned doc (KD1, Low).

## Section 5 (feature/usability/maintainability) — all eight personas
- QA/QC (1): behavior consistent; 101 tests green; error paths handled. No new defect.
- Testing (2): coverage strong; only Low colspan test gaps (T1-T3, from S3).
- UI/UX (3): consistent terminology (verbs mirror flags); helpful errors; theme demo now borderless/unquoted. Good feedback on actions.
- Architect (4): single 4059-line module is large but cohesive; general-case mechanisms (themes, styling coords, colspan, combine); pre-parse CLI dispatch avoided heavier subparsers (KISS). Optional future: module split (M, Low, not required).
- Software engineer (5): clean resource handling; loose type hints (S1-Q1) the main maintainability smell.
- Power user (6): scriptable CLI, STDIN pipeline, themes savable/reusable, `--show-code` generates code, dtype/precision control, escape hatches (`wrap=False`, `on_wrap_conflict`). Well-served.
- Novice (7): `pip install vistab`, `vistab show styles`, README Quick Start → first success without a manual. Strong.
- Stakeholder (8): delivers its stated goal (lightweight, correct, self-documenting table rendering). Main stakeholder-facing gap: version not bumped for the shipped feature set (S1-BUG1).

## Section 6 (compatibility/packaging/release)
- Operator/stakeholder: install path clear (`pip install vistab`, `[cjk]` extra documented); CI proves cross-platform (Linux+Windows) × Python 3.9-3.13; secret-scan CI present. First-run: `vistab` + STDIN or `vistab file.csv` works. The one operator-facing gap: shipping as 1.1.3 despite a v1.2.0 feature set (S1-BUG1) — version pinning would mislead.
- Software engineer: 3.7/3.8 claimed but untested (CI1); code is 3.7-syntax-safe. No breaking API change this cycle (colspan/verbs are additive; apply_theme retained as alias) — backward compatible.

## Section 8 — Eight-persona final sign-off
1. QA/QC: ACCEPT — 105 tests green, no defects; error paths handled.
2. Testing/regression: ACCEPT — strong suite + fixtures; colspan gaps now closed (A3).
3. UI/UX: ACCEPT — consistent CLI verbs/flags, self-documenting errors, cleaner theme demo.
4. Architect: ACCEPT — cohesive single-module design; deferred split (D1) is not a blocker; ARCHITECTURE.md aids orientation.
5. Software engineer: ACCEPT (with note) — clean code/resources; loose type hints (D2) deferred, runtime-harmless.
6. Power user: ACCEPT — scriptable, themeable, escape hatches, pipeline support.
7. Novice: ACCEPT — install + first success from README/CLI without a manual.
8. Stakeholder: ACCEPT — delivers its goal; version now honestly reflects the shipped feature set (v1.2.0).
No persona raises a release blocker.
