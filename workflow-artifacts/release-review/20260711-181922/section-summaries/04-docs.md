# Section 4 - Docs / specs / examples (DEEP: PyPI link portability)

## What I did
- Enumerated every link in `README.md` (the PyPI `long_description`). Found relative
  cross-doc/license links on lines 1, 11, 34, 35, 386, 390, 393 (nav bars + inline + license).
  Images were already absolute but pointed at `/main/` (unpinned).
- Confirmed the mechanism: PyPI renders README as `long_description` but does not resolve
  relative repo paths, so these render as broken links on the package page (the reported
  v1.1.3 problem).
- Confirmed only `README.md` is `long_description` (pyproject `readme = "README.md"`), so the
  nav bars in `docs/*.md`/`FUNCTIONAL_SPEC.md`/`CHANGELOG.md` are NOT PyPI-shipped and are
  correct as relative GitHub navigation (S4-DOC3: no change).
- Fixed (S7): rewrote all README relative doc/license links to absolute
  `https://github.com/fariello/vistab/blob/v1.2.0/...` and repinned the 9 image URLs from
  `/main/` to `/v1.2.0/`. Result: 0 relative links, 25 v1.2.0-pinned URLs in the shipped
  long_description (verified in built wheel METADATA).
- Fixed CHANGELOG (S4-DOC4): folded `[Unreleased]` (bidi, showcase, colspan max_width,
  CLI.md link) into `[1.2.0]` since that content ships AS 1.2.0; consolidated duplicate
  Added/Changed/Fixed subsections.
- Fixed 2 pre-existing em dashes in README (repo prose convention: no em dashes).

## Why
The maintainer's core release concern: broken PyPI links. Pinning to the release tag (not
`/main/`) satisfies "tied to the specific release version" and prevents future drift/404s.

## What I considered but did NOT do
- Did not convert `docs/*.md` nav bars to absolute: they are GitHub-only in-repo navigation;
  absolute would break branch/local navigation and they are not shipped to PyPI.
- Did not add a docs-link CI linter (possible follow-up; not a release blocker).
