# 10 Validation Results
- `python -m pytest -q` before changes: **101 passed**.
- After A1/A2 (version bump + requires-python): **101 passed**; `vistab --version` -> `vistab 1.2.0`.
- After A3/A4 (tests + ARCHITECTURE.md): **105 passed** (4 new colspan interaction tests).
- CLI spot-checks: `vistab show styles/themes`, verb/flag parity — all clean (S4).
- Secrets scan (S2): builtin + gitleaks, 290 low false positives, no real secret/PII.
- No new deprecation warnings; suite warning-free.
UNVERIFIED: `python -m build` (build tool not installed) — pyproject validity confirmed via tomllib+ast parse instead. Python 3.7/3.8 support (now moved out of scope by raising floor to 3.9).
