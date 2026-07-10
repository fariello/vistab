# Cold-Start Orientation Assessment

Question: could a no-context engineer or LLM orient from the project's own tracked docs?

| Knowledge area | Home | Verdict |
|---|---|---|
| Intent, goals, audience, scope | README.md top + FUNCTIONAL_SPEC §1 (Purpose/Scope) | **Good** — clear one-line intent + features + purpose/scope section. |
| Philosophy / principles | (none explicit) | **Adequate** — inferable from design + honest docs; no dedicated file (see guiding-principles KD, low). |
| Architecture / approach | FUNCTIONAL_SPEC §4 (APIs/responsibilities), §13 (component relationships) | **Adequate** — SPEC covers the linear ingest→format→draw pipeline and major components; no dedicated ARCHITECTURE.md (KD1, Low). |
| Decision rationale | .agents/plans/executed/ (10 IPDs), CHANGELOG | **Adequate-but-hidden** — rich rationale exists but in a framework dir a casual reader may not open; not linked from project docs (KD1). |

**Recovered intent (from this session, guarded secondary source):** vistab aims to be a
lightweight, dependency-minimal, ANSI/CJK-width-correct terminal table renderer that is
self-documenting; colspan/combine/verbs/has_header fixes this session were driven by
usability + correctness (no silent failure) principles. Behavior verified against code.

**Verdict:** A fresh LLM/engineer CAN explain what vistab is for and largely how it's built
from README + FUNCTIONAL_SPEC. The one gap is that architecture/decision rationale has no
obvious project-owned home (KD1, Low) — a thin ARCHITECTURE.md linking SPEC + executed
decisions would close it. Not a release blocker.
