# Evidence - assess self-documentation (reproducible)

No files changed. Commands (read-only), from repo root, PYTHONPATH=src:

## CLI surfaces
- Bare `python src/vistab.py` with redirected (non-TTY) empty stdin -> empty, exit 0 (artifact).
- Bare invocation under a REAL tty via `pty.fork()` -> full usage + verb guide + no-data hint,
  exit 1 (this is the true first-run behavior; src/vistab.py:4104-4112).
- `--help` -> rich library-first usage with command examples + verb guidance.
- `help` verb (no subject) -> usage guidance.
- `show bogus` -> "Unknown show subject" + Available subjects list.
- `-t notatheme` -> "Unknown color theme" + full theme list + "run 'vistab show themes'" tip.
- `/no/such/file.csv` -> clear file-not-found error.
- `--align Z` -> "Alignment 'Z' is invalid. Allowed ... 'l','c','r'."
- `--help | grep` -> `--no-color` (mentions NO_COLOR) and `--no-bidi` both present.
- `printf '' | vistab` -> silent, exit 0 (S1 finding: empty pipe gives no hint).

## Library surfaces
- `vistab.__doc__` -> runnable `from vistab import Vistab` example present.
- `Vistab.__doc__` -> ~1137 chars; has an Example block, but opens with generic prose (S2).
- Docstring coverage: iterated all 52 public methods; 0 missing docstrings.
- `Vistab().draw()` -> None on empty; documented in draw() docstring.

## Code paths
- src/vistab.py:4100 `if not is_config_only and not sys.stdin.isatty() and not target_files`
  routes empty pipes into stream parsing.
- src/vistab.py:4104-4112 the no-data usage hint (only reached when NOT reading a stream).

## Sampling
- Full read of the self-documentation lens and the IPD template. CLI behavior probed by direct
  execution (authoritative). Source inspected by targeted grep + section reads around main().
