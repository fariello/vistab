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
