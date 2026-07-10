# 02 Execution Plan (how the review runs)
- Serial, single continuous pass. Project = one ~4k-line Python module + CLI + tests + docs.
- Lead personas applied per section per 00-run-protocol map.
- Validation command: `python -m pytest` (repo-native). No new tooling.
- Fix Bar: fix by default; defer only on Medium-High+ remediation risk.
- Known entering findings: S1-BUG1 (version drift), S1-Q1 (type-hint noise).
- Sections: 1 done -> 2 quality/sec/edge (+MEM/LIVE) -> 3 tests -> 4 docs -> 5 usability/principles/TODO/8-persona -> 6 packaging/version/CI -> implementation-plan -> 7 impl -> 8 GO/NO-GO + push plan.
- Release decision (version bump) is the key gating item.
