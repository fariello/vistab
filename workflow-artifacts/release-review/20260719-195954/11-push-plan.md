# 11 Push plan
- Branch main, 18 unpushed local commits (this session's assess/plan-review/execute cycles + this review's artifacts).
- Permission to push: NOT yet given. No push performed.
- Recommendation: after the user resolves REL1 (version decision), push main and verify CI green (gh run watch) BEFORE any tag/release. CI has not yet run against these commits.
- Section 9 (tag/GitHub release/PyPI upload) only after explicit GO; per RELEASING.md the USER performs PyPI uploads.
- Suggested (only if permitted): `git push origin main` then watch CI; do NOT tag/publish without the version decision + explicit GO.
