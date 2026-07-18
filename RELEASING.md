[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# Releasing vistab

`vistab` is published to PyPI as the `vistab` package. Releases are deliberate and
human-approved. Tagging, GitHub releases, and PyPI uploads happen only through this process,
never ad hoc.

## Versioning

Semantic versioning, measured from the last PUBLISHED PyPI version (not from a git tag):

- **patch** (`x.y.Z+1`): backward-compatible bug fixes and additive-but-small changes.
- **minor** (`x.Y+1.0`): backward-compatible new features.
- **major** (`X+1.0.0`): backward-incompatible changes.

The version lives in two places that MUST match: `version` in `pyproject.toml` and
`__version__` in `src/vistab.py`. `vistab --version` reports the latter.

## Pre-release checklist

1. Decide the version bump from the actual changes since the last PyPI release (see above).
2. Bump `pyproject.toml` `version` and `src/vistab.py` `__version__` to match.
3. Update `CHANGELOG.md`: add a dated section for the new version with Added / Changed /
   Fixed / Deprecated as applicable. Reconcile it against the commits since the last release
   so every user-facing change is captured.
4. If the README/pyproject reference version-pinned GitHub URLs (for PyPI, which does not
   resolve relative links), repin them to the new tag (e.g. `.../blob/vX.Y.Z/...` and
   `.../raw/vX.Y.Z/...`) so the PyPI project page resolves against the released content.
5. Run the full test suite and confirm green (locally and, once pushed, on CI across the
   supported Python matrix). Paste the actual runner output; never claim an unrun pass.
6. Build and check the distribution:

   ```bash
   python -m build
   python -m twine check dist/*
   ```

   Confirm the built version is correct and the long_description has no broken/relative links.

A `/release-review` run (see `.agents/workflows/release-review/`) performs this verification
systematically and ends with an explicit GO/NO-GO. Release execution is its Section 9 and runs
only after a GO plus an explicit human approval to release.

## Release execution (only after human GO)

1. Ensure `main` is pushed and CI is green on the exact release commit.
2. Tag the release commit and push the tag so the version-pinned URLs resolve:

   ```bash
   git tag -a vX.Y.Z -m "vistab X.Y.Z" <release-commit>
   git push origin vX.Y.Z
   ```

3. Build fresh artifacts (`python -m build`) and upload to PyPI:

   ```bash
   python -m twine upload dist/*
   ```

   The PyPI upload is performed by the maintainer.
4. Optionally publish/update the GitHub release for the tag.

## Notes and cautions

- PyPI versions are immutable: once `X.Y.Z` is uploaded it can never be replaced. Never reuse a
  published version number.
- Do not create or push a git tag, cut a GitHub release, or upload to PyPI outside this process
  or without an explicit human go.
- If a git tag was created before the final release commit, move it to the release commit before
  publishing so the tagged tree matches what ships (safe only while that version is not yet on
  PyPI).
