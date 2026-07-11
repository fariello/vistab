# Section 6 - Compatibility / packaging / release (DEEP)

## What I did
- Read `pyproject.toml`. Confirmed version 1.2.0 consistent with `__version__` in
  `src/vistab.py`. Established the correct semver: PyPI latest published is 1.1.3; cumulative
  changes since are additive => 1.2.0 (no bump; corrects an initial mis-finding that proposed
  1.3.0 by measuring from the git tag instead of PyPI). See DEC-1.
- Found and fixed (S7): generic pyproject `description` -> capability-accurate summary;
  added `[project.urls]` (Homepage/Documentation/Source/Changelog/Issues) so the PyPI sidebar
  links exist, all absolute and version-pinned where doc-specific.
- Built sdist + wheel and ran `twine check`: BOTH PASSED. Verified the wheel METADATA embeds
  the Project-URLs and that the shipped long_description has 0 relative links and 25
  v1.2.0-pinned URLs.
- Identified the stale-tag risk (S6-REL1): the existing `v1.2.0` git tag is 9 commits behind
  HEAD and lacks the bidi feature and the hero PNG, so version-pinned README URLs would 404
  against it. Resolution is a RELEASE-CHECKLIST step (move the v1.2.0 tag to the release
  commit before upload), safe because 1.2.0 was never on PyPI. Not a code change.

## Why
The release target is a clean PyPI 1.2.0 with a correct, self-contained package page.

## What I considered but did NOT do
- Did not upload to PyPI or move/push the tag: publishing and remote tag operations are the
  maintainer's, and require explicit approval (Section 9). Recorded as release steps.
- Did not add trusted-publishing/release CI: out of scope for this focused review; possible
  follow-up.
- Did not change `requires-python` (>=3.9) or dependencies: no evidence they are wrong.
