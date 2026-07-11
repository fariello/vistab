# Decisions - Release Review 20260711-181922

## Scope
Focused release review triggered by the maintainer's specific concern: PyPI renders
`README.md` as `long_description` but does NOT resolve relative repo links, so v1.1.3's
README cross-doc/license links are broken on the PyPI page. Extra depth on Section 4 (docs)
and Section 6 (packaging/release). Framework dirs (`.agents/workflows/`) and
`workflow-artifacts/` are out of review scope per protocol.

## DEC-1: Next PyPI version is 1.2.0 (NOT 1.3.0). Corrects an initial mis-finding.
- PyPI latest PUBLISHED = 1.1.3 (maintainer-confirmed). Semver is measured from the last
  published baseline, not from a git tag.
- Since 1.1.3, changes are all additive/backward-compatible (colspan + `set_cell_span`,
  `set_color`/`--no-color`, `set_bidi`/`--no-bidi`, `show showcase`, colspan `max_width`
  fix) => minor bump 1.1.3 -> 1.2.0. pyproject.toml and `__version__` already say 1.2.0.
- Therefore: NO version bump. My initial finding proposing 1.3.0 was anchored to the git
  tag rather than the published baseline; it is corrected and superseded (S6-REL1b).

## DEC-2: Pin README's PyPI-facing links to the release tag v1.2.0 (absolute GitHub URLs).
- Only `README.md` is `long_description` (pyproject `readme = "README.md"`), so ONLY its
  relative links break on PyPI. Fix those.
- Use absolute URLs pinned to the version being released, `.../blob/v1.2.0/...` for docs and
  `.../raw/v1.2.0/...` (equivalently `raw.githubusercontent.com/.../v1.2.0/...`) for images,
  so the PyPI page for 1.2.0 always shows 1.2.0 content (the maintainer's "tied to the
  specific release version" requirement).
- The nav bars inside `docs/*.md`, `FUNCTIONAL_SPEC.md`, `CHANGELOG.md` stay RELATIVE: they
  are correct for in-repo GitHub navigation and are not shipped to PyPI (S4-DOC3). Changing
  them to absolute would break local/branch navigation. Left as-is by design.

## DEC-3: The v1.2.0 tag must be MOVED to the release commit at publish time.
- Current v1.2.0 tag is 9 commits behind HEAD and does not contain the bidi feature or
  `docs/assets/vistab-show-showcase-01.png`. Pinning README URLs to v1.2.0 while the tag is
  stale would 404 the hero image.
- Safe to move: 1.2.0 was never uploaded to PyPI. This is a RELEASE-CHECKLIST step (retag +
  push tag before/at upload), not a code change. Recorded for Section 8 Go/No-Go.

## DEC-4: Add [project.urls] and improve the pyproject description.
- Low risk, high value for PyPI page (sidebar links + accurate summary).
