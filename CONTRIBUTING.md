[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Contributing to vistab

Thanks for your interest in improving `vistab`. This document covers how to set up, test,
and propose changes.

## Project shape

- `vistab` is a pure-Python library plus a CLI, implemented in a single module: `src/vistab.py`.
- The only runtime dependency is `wcwidth`; `cjkwrap` is an optional extra (`vistab[cjk]`).
- Tests live in `tests/` and use the standard-library `unittest` framework (also runnable with
  `pytest`).

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .[dev]         # installs vistab + pytest
```

## Running the tests

Use whichever runner you prefer; CI runs the `unittest` form across Python 3.9-3.13:

```bash
python -m pytest -q            # local convenience
python -m unittest discover tests/   # exactly what CI runs
```

When you report that tests pass, paste the actual runner output. Do not claim a pass you did
not run.

### Test across Python versions

Some bugs only appear on the CI matrix (Python 3.9-3.13, ubuntu + windows), not on a single
local interpreter. Two known classes:

- **Annotation evaluation.** Python 3.14 defers annotation evaluation (PEP 649); 3.9-3.13
  evaluate at definition time. An unimported name used only in an annotation passes on 3.14 but
  raises `NameError` at import on older versions. Prefer testing in a clean venv on an older
  interpreter before relying on green.
- **Stdio encoding.** Under a POSIX `C`/`POSIX` locale, older Pythons default stdout to ASCII;
  the CLI reconfigures its streams to UTF-8 to stay safe. Do not remove that.

## Code style and conventions

- Keep the library dependency-light and the design KISS. Prefer the general case over
  special-casing.
- Documentation must describe what the software actually does today (honest docs).
- In authored Markdown, do not use em or en dashes; use commas, periods, or parentheses.

## Making changes

1. Work on a branch off `main`.
2. Add or update tests for any behavior change. Regression fixtures live in `tests/fixtures/`.
3. Update `CHANGELOG.md` under the appropriate version section (Added / Changed / Fixed /
   Deprecated). Every user-facing change belongs there.
4. Keep public API changes backward compatible where possible; call out breaks clearly.

## Commits

- Commit only the files you changed, path-scoped: `git commit -m "message" -- <paths>`.
- Do not use `git add -A`, a bare `git add`, or `git commit -a`.
- Never commit secrets; `.gitignore` excludes common credential patterns and secret scanning
  runs in CI.

## Plan / IPD lifecycle (for agent-assisted work)

This repo uses reusable agent workflows under `.agents/workflows/` and an
Implementation-Plan-Document (IPD) lifecycle under `.agents/plans/`. If you (or an agent) plan a
non-trivial change:

- Write the proposal as a dated IPD in `.agents/plans/pending/`, named
  `YYYYMMDD-HHMM-NN-<slug>.md`.
- Each IPD carries a front-matter `Status:` progressing `draft` -> `to-review` -> `reviewed` ->
  `approved`, then a terminal status mirroring its directory, plus an appended
  `## Workflow history` section.
- After human approval and implementation+verification, move it (`git mv`, never a silent
  delete) to a terminal directory:
  - `.agents/plans/executed/` - implemented, verified, and tested.
  - `.agents/plans/superseded/` - replaced by a better plan (add a `RETIRED YYYY-MM-DD: ...;
    superseded by <path>` header).
  - `.agents/plans/not-executed/` - deliberately decided against, no replacement.
  - `.agents/plans/reusable/` - recurring runbooks meant to be re-run.
- Do not add commits to a plan already in `executed/`; close a post-execution gap with a new
  corrective IPD.
- Immortalize research you relied on to `.agents/docs/research/` and narrative walkthroughs to
  `.agents/docs/walkthroughs/` (`...-walkthrough.md`).

## Releasing

Releases follow `RELEASING.md`. Tagging, GitHub releases, and PyPI uploads happen only through
that process after an explicit human go; do not tag or publish ad hoc.
