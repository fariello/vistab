# Final Release Review Report — vistab v1.2.0 (run 20260711-122840)

Focused re-review after the prior GO (20260710-194844). Scope: the delta since that review
(library-first framing docs + the CLI-polish batch: --no-color/NO_COLOR, show span parity,
span-demo redesign, library messaging).

## Completed actions
| ID | Description | Files | Commit | Validation |
|----|-------------|-------|--------|------------|
| A1 | Fix: `show styles --no-color` no longer leaks a bold-title escape | src/vistab.py | 53703c8 | escape-free |
| A2 | Fix: `show capabilities --no-color` now emits the color-off WARNING (its colored content is the wrapping demo, so content stays colored; chrome honors --no-color) | src/vistab.py | 53703c8 | warning printed |
| A3 | Tests: `show span` / `show spans` verb-parity coverage | tests/test_cli.py | 53703c8 | pytest 113 |
| A4 | Tests: `--no-color` / `NO_COLOR` / `set_color` (feature was untested) incl. color-ON byte-identical pin + user-content preservation | tests/test_cli.py | 53703c8 | pytest 113 |
| A5 | CHANGELOG: fold `[Unreleased]` items into `[1.2.0]` (release honesty) | CHANGELOG.md | 53703c8 | inspect |

## Identified but not addressed
| ID | Description | Remediation Risk + axis | Reason | Next step |
|----|-------------|-------------------------|--------|-----------|
| (none) | All findings fixed in-run. | - | - | - |
Deferred from the prior review remain deferred (module split, type-hint overhaul; Medium-High/Medium complexity). No new deferrals.

## Fix Bar summary
5 findings, all Low remediation risk, all fixed. No finding silently dropped; nothing skipped for effort/cost.

## Tests / validation
| Check | Result |
|-------|--------|
| `python -m pytest` | 113 passed (was 105; +8) |
| Color-ON regression pin (themed + coordinate styling vs prior GO tip 373329f) | byte-identical |
| `--no-color` / `NO_COLOR` themed render | escape-free |
| Demo `--no-color` sweep | styles/colors/themes/anatomy/span escape-free; capabilities intentionally colored (it demonstrates ANSI wrapping) + warning |
| Secrets | unchanged since prior GO (no new secret surface) |

## The one nuance worth stating plainly
`show capabilities` is **inherently colored even under `--no-color`**: its cell content is
ANSI-colored on purpose to demonstrate that vistab wraps colored text correctly. Stripping
it would destroy the demo. The fix keeps that content colored but prints
`WARNING: colors turned off ...` so the behavior is honest, not silent. This is a deliberate
design decision, not an incomplete `--no-color`.

## CI / schema / deprecated-code
Unchanged from prior GO. CI strong (matrix + gitleaks). No schemas. `apply_theme`/`header`
remain intentional documented deprecated aliases.

## TODO / pending plans
`TODO.md` honest (3 future CLI ideas correctly deferred). **No pending agent plans or staged
prompts** (both dirs empty). No pending-plans WARNING.

## Guiding-principles / self-documenting / cold-start
Strong adherence; library-first + --no-color advance intuitive/self-documenting/honest-docs.
`vistab show span` fixes the discoverability trap. Cold-start docs (README, FUNCTIONAL_SPEC,
ARCHITECTURE.md) adequate. No GP violations.

## Eight-persona sign-off
All ACCEPT: QA (113 green), Testing (gaps closed), UI/UX (consistent; --no-color + warning),
Architect (--no-color seam central + gated, byte-identical color-ON), SWE (clean), Power user
(--no-color respects NO_COLOR; scriptable), Novice (show span works; helpful warning),
Stakeholder (v1.2.0 coherent and release-ready).

## Push / release decision
No push/tag/publish performed. v1.2.0 is NOT yet released: no git tag, PyPI still at 1.1.3.
Recommended (explicit approval required): push main, tag v1.2.0 + push tag, then PyPI publish
(Section 9). See 11-push-plan.md.

## GO / NO-GO
**GO** for the v1.2.0 release. The delta is correct, byte-compatible for default output,
newly test-covered, and documented. The two findings this run surfaced (B1/U1) are fixed.

## Restart
No restart (loop guard: this run is itself the targeted follow-up to 20260710-194844).
Changes were small, safe, validated.

## Section 9 readiness
Ready. Tag + PyPI publish await your explicit approval.
