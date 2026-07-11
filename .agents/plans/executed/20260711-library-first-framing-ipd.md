# Implementation Plan - Make vistab read as a LIBRARY first (docs/docstring framing)

Status: PROPOSED (not yet executed)

> **Plan-review note (2026-07-11, revisions applied).** Claims verified against the
> actual files. The proposed docstring example (`Vistab(header=[...])`, `add_row`,
> `set_cols_align`, `draw()`) was executed and renders correctly. It is accurate, not
> aspirational. Two current-state corrections were folded in so the implementer makes the
> real delta, not a no-op: (a) the README "Detailed Documentation" list **already** puts
> the API reference before the CLI, so that "reorder" is largely done; the remaining work
> is adding an import quickstart above the CLI content and labeling the CLI as secondary;
> (b) `pyproject.toml` description **already** leads with "module", so §4's pyproject item
> is already satisfied. Also hardened the AGENTS.md placement guardrail and added
> CHANGELOG/doctest checks to Verification.

Reframe vistab's docs, module docstring, and AGENTS.md so that a human or coding
agent encountering the repo (or the installed module) concludes "this is a
Python library I should import" BEFORE "this is a command-line tool I should
shell out to."

---

## Motivation (observed problem)

vistab is an importable library (`from vistab import Vistab; ...; print(t.draw())`)
that also ships a CLI. Across multiple sessions and multiple downstream projects,
coding agents (including Claude Opus 4.8) have repeatedly reached for the vistab
CLI, piping data through the `vistab` command, instead of importing `Vistab` and
calling its API. That is slower, harder to test, and fragile.

Root cause is framing/discoverability, not the code:
- The module docstring's first line ("module for creating simple ASCII tables")
  is fine but does not immediately anchor "import this class".
- The README top nav lists `[CLI]` as one of five equal links, giving the CLI
  visual parity with the library.
- Nothing in AGENTS.md tells an agent "prefer importing vistab over invoking the
  CLI".
- When a project merely has a `vistab` binary on PATH (and vistab shows up only
  as a dependency or a directory name), an agent that does not read the API doc
  first defaults to "a command exists, use the command".

The goal: put unmissable "import me" signals in the first thing each audience
reads (module docstring, README top, AGENTS.md), so the library path is the
obvious default and the CLI is clearly the secondary, special-purpose surface.

---

## User Review Required

> [!IMPORTANT]
> - This is a DOCS/FRAMING change only. Do NOT change vistab's public API, CLI
>   behavior, or table rendering. Existing tests must stay green.
> - The CLI stays fully documented; it is just repositioned as the secondary
>   surface, not removed or demoted in capability.

---

## Proposed Changes

### 1. Module docstring (`src/vistab.py`, top-of-file `"""..."""`)

Rewrite the opening so the FIRST lines establish "importable library" with a
copy-pasteable import + `.draw()` example, and explicitly point at the CLI as
secondary. Suggested opening shape:

```
vistab - a Python LIBRARY for building aligned, color-aware text tables.

Import it and call the API; do not shell out to the CLI for programmatic use:

    from vistab import Vistab
    t = Vistab(header=["Name", "Age"])
    t.add_row(["Sarah", 27])
    t.set_cols_align(["l", "r"])
    print(t.draw())

A command-line entry point also exists for ad-hoc CSV/terminal use (see
docs/CLI.md), but in Python code prefer `from vistab import Vistab`.
```

Keep the existing detailed examples below this opening.

### 2. README (`README.md`)

- The very first content line (currently the nav row `[README] | [API] | [CLI]
  | [SPEC] | [CHANGELOG]`) and the opening paragraph should foreground "Python
  library / import" and show the `from vistab import Vistab` quickstart ABOVE
  the CLI reference. **Note (verified current state):** the "Detailed Documentation"
  list at README.md:16-20 **already** places the Python API reference (line 19) before
  the CLI manual (line 20), so no reorder is needed there. The real remaining work is
  (i) adding the `from vistab import Vistab` quickstart high in the README, above any CLI
  content, and (ii) explicitly labeling the CLI manual line as the secondary/ad-hoc
  surface. Do not perform a no-op reorder.
- Add a short, explicit line near the top such as: "Using vistab from Python?
  Import `Vistab` (see the API reference). The CLI is for ad-hoc terminal/CSV
  use only."

### 3. AGENTS.md (add an agent-facing usage note)

Add a short section telling coding agents the intended default. **Placement guardrail:**
put it **outside** (above or below) the `<!-- AGENT-WORKFLOWS:BEGIN --> ... <!--
AGENT-WORKFLOWS:END -->` markers. Anything inside those markers is auto-managed and will be
**overwritten** by the agent-workflows installer on its next run, so an in-block edit would
be silently lost. Suggested content:

> ## Using vistab in code
> vistab is a Python library. To render tables programmatically, `from vistab
> import Vistab` and use its API (`add_row`, `set_cols_align`, `color_row`,
> `set_theme`, `draw()`, ...). Do NOT invoke the `vistab` CLI via subprocess for
> programmatic table building; the CLI exists only for ad-hoc terminal/CSV use.

### 4. Optional reinforcement (low-risk, nice-to-have)

- `pyproject.toml` project description: **already satisfied** (it reads "A simple module
  for creating ASCII tables", leading with "module" not CLI, verified at pyproject.toml:8).
  No change needed for the library-first goal. (Separately, "simple ASCII tables" undersells
  the ANSI/Unicode/CJK/color/colspan capability, but improving the description's *accuracy*
  is out of scope for this framing IPD; leave it or handle in a separate docs pass.)
- If `vistab --help` / the CLI docstring is the first thing a CLI-curious user
  sees, add one line there too: "vistab is primarily a Python library; this CLI
  is for ad-hoc use. In code, `from vistab import Vistab`."

---

## Non-goals

- No API, CLI, or rendering behavior changes.
- Not removing or hiding the CLI; it stays a documented, supported surface.

---

## Verification

- Existing test suite stays green (docs-only change): `python -m pytest`.
- **Execute the new docstring example** to confirm it renders (it is code in a docstring,
  so it must actually work. The reviewer confirmed the proposed snippet renders a valid
  header table). Copy the example out and run it, or add it as a doctest; either way do not
  ship an example that has not been run.
- **CHANGELOG:** add a one-line `[Unreleased]` entry noting the library-first docs/framing
  update (the module docstring and README opening are user-visible), to keep the changelog
  honest.
- Manual read-through: the module docstring's first ~10 lines, the README's
  first screen, and AGENTS.md each make "import the library" the obvious first
  conclusion, with the CLI clearly secondary.

## Prose convention

No em dashes in authored prose (match the repo/AGENTS.md convention); use
periods, commas, colons, or parentheses.
