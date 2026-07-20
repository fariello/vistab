# 05 Decisions

- Subject = target project vistab; framework dirs (.agents/workflows, .opencode, .claude) and workflow-artifacts EXCLUDED from review scope per 00-run-protocol.
- No GUIDING_PRINCIPLES.md -> universal fallback principles (intuitive/self-documenting, general-case/configurable, KISS, honest docs). Recorded.
- Parallel audit lanes: NOT engaged. Single ~4500-line module + tests + docs is effectively one tightly-coupled surface; the reviewer also holds deep prior context from this session's assess/plan-review/execute cycles. Serial is appropriate (fan-out would be overhead). Recorded per auto-parallel convention.
- Pre-flight gate: CLEAN. .agents/plans/pending/ holds only .gitkeep + README (all IPDs executed); no staged prompts; TODO.md is a forward roadmap with no release-blocker items. No real signal -> skipped the interactive ask and proceeded silently (verdict-free, per protocol).
- Conversation context (this session) used as a guarded secondary source for intent; behavior claims verified against code/tests/live runs.
- draw() empty-table behavior: verified the executed E1 fix (returns "") against live runs and docs; not re-litigated.
- Version decision (REL1) is deferred to the human: the reviewer does not pick the version number or tag/publish (per RELEASING.md + protocol: no publish without explicit GO).
