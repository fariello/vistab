# 11 Push / Release plan
- Branch main == origin/main (user already pushed; 0 ahead/behind before this run).
- This run added 1 commit (53703c8, S7 fixes) + the run artifacts commits -> now local ahead of origin by those.
- v1.2.0 release NOT done: no git tag (repo has 0 tags), PyPI still at 1.1.3.
- Recommendation (all gated on explicit approval):
  1. git push origin main   (publish this run's commits)
  2. git tag v1.2.0 && git push origin v1.2.0   (first-ever tag)
  3. PyPI publish: python -m build && twine upload dist/*  (Section 9; first publish of 1.2.0)
- No push/tag/publish performed by this review.
