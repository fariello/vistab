# Assessment run report - documentation

- Date / run ID: 20260709-230111
- Concern: documentation
- Scope: whole project
- IPD written: [.agents/plans/pending/20260709-assess-documentation.md](file:///home/gfariello/VC/vistab/.agents/plans/pending/20260709-assess-documentation.md)
- Verdict: needs work for documentation

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| DOC-01 | High | Low | Software Engineer | CLI internally invokes deprecated `apply_theme` causing warnings during regression check executions. |
| DOC-02 | Medium | Low | Complete Novice | The public documentation (README and API Reference) advertise the deprecated `apply_theme` instead of the current `set_theme`. |
| DOC-04 | Medium | Low | Developer / Maintainer | The roadmap (`TODO.md`) contains outdated references listing Colspan as a future item when it is already fully implemented. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

- Clean up deprecated references by replacing all instances of `apply_theme` with `set_theme` across source code, CLI, tests, examples, README, and API documentation.
- Update `--show-code` CLI generator and the corresponding regression fixture file to output `set_theme` calls.
- Fix docstring for `Vistab.__init__` to reference `set_header` instead of deprecated `header()`.
- Update `TODO.md` roadmap and correct version reference headers in `docs/API.md`.

## Deferred (with reason)

None.

## Out-of-repo / organizational notes (if any)

None.

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before execution. This workflow does not execute the plan.
