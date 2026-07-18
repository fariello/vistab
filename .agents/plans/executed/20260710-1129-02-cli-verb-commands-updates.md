# Updates to CLI Verb Commands IPD

We have reviewed [.agents/plans/pending/20260710-cli-verb-commands.md](file:///home/gfariello/VC/vistab/.agents/plans/pending/20260710-cli-verb-commands.md) and identified the following refinements and additions that should be incorporated into the execution plan.

## Proposed Updates

### 1. Update/Regenerate `regression_diagnostic_matrix.txt` (Refinement to Step 5)
- **Why**: Step 5 of the plan updates `print_themes_demo` to render inner sample tables with `padding=0`. This change alters the horizontal width and characters of the theme demo grid output. The existing regression test `test_demo_themes` validates the stdout of `vistab --demo themes` against `tests/fixtures/regression_diagnostic_matrix.txt`. If this fixture is not updated, the test suite will fail.
- **What**: Explicitly include the regeneration/update of the `tests/fixtures/regression_diagnostic_matrix.txt` fixture in Step 5 alongside the code modification.

### 2. Include Aliases in `--demo` Argument Choices (Refinement to Step 6)
- **Why**: Step 6 adds `"span"` to the `--demo` argparse choices. To maintain 100% parity and consistency between the verb-based commands and flag-based aliases, the `--demo` flag should also support the exact same aliases as the `demo` command (`colspan`, `rowspan`, `caps`).
- **What**: Update the `--demo` choice list in argparse to include `["styles", "colors", "capabilities", "caps", "anatomy", "themes", "span", "colspan", "rowspan"]` and resolve them to their canonical renderers.

### 3. Length Guard on sys.argv in Pre-Parse Dispatch (Safety in Step 2)
- **Why**: Accessing `sys.argv[1]` without checking bounds will raise an `IndexError` if the CLI is run with no arguments (e.g. `vistab` or `python src/vistab.py`).
- **What**: The pre-parse dispatch logic must check `len(sys.argv) > 1` before evaluating if `sys.argv[1]` matches one of the reserved verbs.
