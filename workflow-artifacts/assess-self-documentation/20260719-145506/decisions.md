# Decisions & assumptions - assess self-documentation

## Concern / scope
- Concern: self-documentation (in-product learn-as-you-go clarity; distinct from repo docs).
- Scope: whole product surface: CLI (help/usage/errors/first-run) + library (docstrings, error
  messages). Version 1.2.1.
- Lens lead personas: complete novice (primary), UI/UX engineer, power user.

## Method (verified, not inferred)
- Executed the CLI across surfaces: bare invocation, --help, help verb, unknown show subject,
  unknown theme, missing file, bad --align/--dtype, --no-color/--no-bidi presence.
- CRITICAL correction: an initial "bare vistab is silent (exit 0)" observation was a NON-TTY
  test artifact (redirected stdin routes into empty stream parsing). Re-ran under a pseudo-tty
  (pty.fork) to emulate a real interactive terminal: bare vistab prints full usage + guidance
  and exits 1. The finding was disproved and NOT carried into the IPD.
- Library: inspected module + class docstrings; programmatically checked docstring coverage of
  all public methods (52/52 present); checked draw() empty behavior + its docstring.

## What was intentionally NOT proposed and why
- No interactive prompts, REPL, or first-run tutorial: the product already teaches well; adding
  such surface would violate KISS/Complexity axis.
- The bare-vistab "silence" was not proposed because it is not real on a TTY (disproved).
- draw() returning None on empty is documented in its docstring, so not flagged as a trap.

## Open questions
- S1 exit code (assume 1, matching the existing TTY no-data path) and whether a header-only /
  zero-data-row input should also hint (recommend: only hint when NO parseable row exists, so a
  legitimate header-only render is unaffected).
