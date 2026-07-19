# Assessment - self-documentation (whole product)

Verdict: **strong** for self-documentation (in-product, learn-as-you-go clarity).

IPD written: `.agents/plans/pending/20260719-1455-01-assess-self-documentation.md`

Run ID: 20260719-145506. Version assessed: 1.2.1.

## What is strong (verified by execution, not asserted)

- **First-run on a real TTY:** bare `vistab` prints usage + verb guide + "provide a file or pipe
  data" + a `--help` tip and exits 1 (verified under a pty; the "silent bare vistab" suspicion
  was a non-TTY test artifact and was DISPROVED).
- **`--help`:** rich, accurate, library-first, with command examples and verb guidance.
- **Errors that teach:** unknown `show` subject -> lists subjects; unknown theme -> lists all
  themes + a tip; bad `--align`/`--dtype` -> names valid codes (dtype explains each).
- **Discoverability:** `--no-color`, `--no-bidi`, and the `show`/`help`/`demo` verbs surface in
  `--help`.
- **Library:** module + class docstrings carry runnable `from vistab import` examples; all 52
  public methods have docstrings; `draw()` documents its `None`-on-empty return.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| S1 | Low | Low | novice | Piped-but-EMPTY stdin exits 0 silently; the helpful "no data" hint only fires on a TTY, so `printf '' \| vistab` (or an upstream command that produced nothing) gives no guidance. |
| S2 | Low | Low | novice | `Vistab` class docstring opens with generic boilerplate before its Example block; lead with purpose + the runnable snippet (match the module docstring). |

## Proposed plan (summary)

1. S1: emit the existing "no tabular dataset found ... see 'vistab --help'" hint and a non-zero
   exit when the input stream yields zero rows (empty pipe/file), instead of silent exit 0. Add a
   CLI test; keep TTY-no-args and successful renders unchanged.
2. S2: reorder the class docstring so purpose + a runnable example appear first.

## Deferred (with reason)

None. Both findings are Low Remediation Risk (small CLI + docstring changes). Nothing dropped.

Next step: review the IPD (optionally run plan-review on it) and approve before execution.
This workflow does not execute the plan.
