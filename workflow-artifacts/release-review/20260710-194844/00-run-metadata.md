# 00 Run Metadata

- **Run ID:** 20260710-194844
- **Workflow:** release-review
- **Agent/model:** opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- **Repository:** /home/gfariello/VC/vistab
- **Subject:** the `vistab` project (framework files under `.agents/workflows/` and `workflow-artifacts/` are out of review scope)
- **Git:** yes
- **Initial branch:** main
- **Head commit:** 922e17b4a131f53158c101c78c01af42f0ed0519
- **Remote:** origin git@github.com:fariello/vistab.git
- **Initial working tree:** clean
- **Unpushed commits:** 15 (main ahead of origin/main)
- **Python:** 3.14.6
- **Test baseline at run start:** 101 passed
- **Mode:** full review, serial (single-module ~4k-line project; parallel lanes not warranted)
- **`workflow-artifacts/` git-ignored:** no (artifacts will be committed)

## Environment summary
Pure-Python terminal-table library + CLI. Single module `src/vistab.py` (4059 lines),
console entry point `vistab = "vistab:main"`, optional `[cjk]` extra, dep `wcwidth`.
Tests: 7 test files (test_vistab, test_cli, test_config, test_demo, test_edge,
test_regression, test_streaming). Docs: README, docs/API.md, docs/CLI.md,
FUNCTIONAL_SPEC.md, CHANGELOG.md, TODO.md.
