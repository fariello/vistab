# Implementation Plan (S7) — RUN 20260711-122840 (focused re-review)
All Low remediation risk; fix by default.
| # | Action | Source | Files | Validation |
|---|---|---|---|---|
| A1 | Route print_styles_list bold title through _demo_text (honor --no-color) | B1 | src/vistab.py | show styles --no-color: no escapes |
| A2 | print_test_demo (capabilities): emit color-off warning + keep colored content (color is the demo); gate its title | U1 | src/vistab.py | show capabilities --no-color prints warning; documented as inherently colored |
| A3 | Add CLI tests: show span / show spans parity | T1 | tests/test_cli.py | pytest |
| A4 | Add tests: set_color(False) no styling escapes + color-ON pin; --no-color/NO_COLOR escape-free + warning | T2 | tests/test_vistab.py or test_cli.py | pytest |
| A5 | Fold [Unreleased] items into [1.2.0] in CHANGELOG (release honesty) | A1(S6) | CHANGELOG.md | inspect |
Deferred: none (all Low RR).
