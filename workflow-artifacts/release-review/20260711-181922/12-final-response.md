# Release Review 20260711-181922 - Final Report

Focus: PyPI documentation-link portability (maintainer's stated concern) plus packaging
metadata for a clean 1.2.0 PyPI release. Scope emphasized Sections 4 (docs) and 6 (packaging).

## 1. Completed actions

| ID | What was done | Files | Commit | Validation |
|----|---------------|-------|--------|------------|
| S4-DOC1 | Rewrote all README relative doc/license links to absolute `github.com/.../blob/v1.2.0/...` | README.md | (this run) | 0 relative links in shipped long_description |
| S4-DOC2 | Repinned 9 README image URLs from `/main/` to `/v1.2.0/` | README.md | (this run) | 25 v1.2.0-pinned URLs in wheel METADATA |
| S4-DOC4 | Folded CHANGELOG `[Unreleased]` into `[1.2.0]`; consolidated duplicate Added/Changed/Fixed | CHANGELOG.md | (this run) | one clean section set |
| S6-REL2 | Rewrote pyproject `description` to a capability-accurate summary | pyproject.toml | (this run) | twine check PASSED |
| S6-REL3 | Added `[project.urls]` (Homepage/Documentation/Source/Changelog/Issues), absolute + pinned | pyproject.toml | (this run) | Project-URL in METADATA |
| (prose) | Removed 2 pre-existing em dashes in README (repo convention) | README.md | (this run) | 0 em dashes |

Validation: `pytest` 135 passed; `python -m build` succeeded; `twine check` PASSED on sdist +
wheel; wheel METADATA verified to embed Project-URLs and a relative-link-free long_description.

## 2. Identified but not addressed (deferred / release-step, not code)

| ID | What | RR + axis | Reason | Next step |
|----|------|-----------|--------|-----------|
| S6-REL1 | v1.2.0 git tag is stale (9 commits behind HEAD; lacks bidi + hero PNG) | Low | Not a code change; it is a release-execution action requiring maintainer + remote | At release, MOVE the v1.2.0 tag to the release commit, then push, so pinned URLs resolve |
| S4-DOC3 | `docs/*.md` nav bars are relative | Low (usability) | Correct for in-repo GitHub nav; not shipped to PyPI; absolute would break local/branch nav | No change (by design) |

## 3. Correction made during the review
Initial finding proposed bumping to 1.3.0. Corrected: semver is measured from the last
PUBLISHED PyPI version (1.1.3), and all changes since are additive => 1.2.0, which is already
set. No version bump. (S6-REL1b supersedes the bump proposal.)

## 4. RELEASE CHECKLIST (maintainer, Section 9 - requires your approval)
The version-pinned README/pyproject URLs point at tag `v1.2.0`. For them to resolve on the
PyPI page and GitHub, the tag must point at the commit you actually ship:
1. Commit these review changes.
2. Move the tag to the release commit: `git tag -f v1.2.0 <release-commit>` and
   `git push -f origin v1.2.0` (safe: 1.2.0 was never on PyPI).
3. `python -m build` then `twine upload dist/*` (you always do PyPI uploads).
4. Optionally update/verify the GitHub v1.2.0 release to match.
If you prefer to NOT force-move a published-looking tag, the alternative is to cut a fresh
patch/minor and repin URLs to it; but since 1.2.0 is unreleased on PyPI, moving the tag is
the clean path.

## 5. Fix Bar summary
All findings were Low remediation risk and fixed by default, except S6-REL1 (a release-time
remote/tag action, not a repo code change) and S4-DOC3 (correct as-is). No finding was
deferred for effort/cost. No High/LIVE/MEM findings.

## 6. Other sections (brief)
- S2 quality/security: recent code, just passed two prior reviews + a bidi feature review; no
  new defects; 0 TODO/FIXME markers in source.
- S3 tests: 135 green; the doc/packaging changes are covered by build + twine + a
  metadata-content assertion performed manually this run.
- S5 usability/maintainability: PyPI page now self-contained (hero image, working links,
  sidebar URLs, accurate summary). Cold-start orientation intact (README/API/CLI/CHANGELOG).
- No pending plans or staged prompts (both IPDs previously moved to executed).

## 7. Go / No-Go
**CONDITIONAL GO** for a 1.2.0 PyPI release. The one condition is the release-checklist tag
move (S6-REL1) so version-pinned URLs resolve; it is a maintainer action, not a repo defect.
The repository content itself is ready: links portable and version-pinned, package builds,
twine check passes.

## 8. Push / no-push
No push performed. Recommendation: commit locally now; the maintainer performs the tag move,
push, and PyPI upload (uploads are always the maintainer's). See release checklist.

## 9. Restart
No restart recommended. Focused scope, all repo-side findings fixed and validated.
