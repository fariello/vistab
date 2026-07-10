# Section 2 — Quality / Security / Edge Cases (per-phase report)
## What I did
Ran the mandatory secrets/PII scan (builtin scan_secrets.py + gitleaks): 290 low-severity heuristic hits, all high-entropy-string matches on README GitHub asset URLs and paths — triaged as false positives; no real secret/PII; no High/Blocker. Traced MEM surfaces by reading code: all file opens are `with`-managed; the only cache is bounded `lru_cache(maxsize=8192)`; no unbounded growth. Traced LIVE surfaces: `stream()` is memoryless (sample-then-yield); `--sort-by` with `--stream` is explicitly rejected (vistab.py:3797) rather than silently buffering — the documented memory tradeoff is enforced. Confirmed no eval/exec/pickle/yaml.load/subprocess/os.system; `set_cols_dtype` Callable runs a user-supplied function (not string eval). CLI top-level `except Exception` is deliberate self-documenting error handling.
## Why
Domain (a rendering lib) has minimal attack/resource surface; the audit confirms that and checks the two real risk areas: the streaming/live path and the ANSI-sanitization security feature.
## Findings raised
- S2-S1 (Low): secrets scan — all false positives (documented, no action).
- S2-MEM1 (n/a): resource/live handling clean.
- (S1-Q1 carried: type-hint noise, maintainability — decide in S7.)
## Considered but did NOT do
- No product fixes (audit-only section).
- Did not attempt to fix the type hints here (deferred to S7 decision; runtime-harmless).
- Did not install trufflehog/detect-secrets (gitleaks already ran; recommend CI scan in S6).
