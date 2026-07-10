# 05 Decisions & Assumptions

- **Scope:** subject is the `vistab` project. `.agents/workflows/` and `workflow-artifacts/` excluded per 00-run-protocol.
- **Guiding principles:** none in repo → universal fallback (intuitive/self-documenting, general-case/configurable, KISS, honest docs) applied and recorded.
- **Parallel audit lanes:** NOT used. Rationale: single ~4k-line module with one cohesive surface; serial review is clearer and lower-overhead. (00-run-protocol allows opting out.)
- **Conversation intent source:** this session's history is rich (colspan design, hardening, CLI grammar, has_header fix) — usable secondary source for cold-start docs; behavior facts still verified against code.
- **Version state (S1-BUG1):** code=1.1.3 but CHANGELOG/TODO describe unreleased v1.2.0 work. Treated as a release prerequisite decision for §6.
