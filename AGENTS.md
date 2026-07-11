# AGENTS

<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

This repository includes reusable agent workflows under `.agents/workflows/`. They are invoked on demand and are NOT always-loaded context. See `.agents/workflows/index.md` for the list and how to run each (native `/commands` in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).

### Guidelines for Antigravity & Other Agents
When requested to run one of these workflows (e.g. "run release-review", "assess <concern>", "run setup-repo", "run scaffold"):
1. Locate the workflow's entry file under `.agents/workflows/` (referenced in `.agents/workflows/index.md`).
2. Read and execute the instructions defined in that workflow file step-by-step.
<!-- AGENT-WORKFLOWS:END -->

## Using vistab in code

vistab is a Python library. To render tables programmatically, `from vistab import Vistab`
and use its API (`add_row`, `set_cols_align`, `color_row`, `set_theme`, `draw()`, ...). Do
NOT invoke the `vistab` CLI via subprocess for programmatic table building; the CLI exists
only for ad-hoc terminal/CSV use.
