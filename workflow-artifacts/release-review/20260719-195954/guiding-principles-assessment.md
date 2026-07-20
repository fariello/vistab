# Guiding-principles adherence (universal fallback; no repo principles doc)

- Intuitive/self-documenting: STRONG. --help, `vistab show showcase`, empty-input guidance+exit 1, clear dtype-code error enumeration, README learn-as-you-go examples.
- General-case/configurable: STRONG. dtype codes, themes, styles, alignment, on_wrap_conflict/on_short_row/on_long_row, colspan; few magic constants.
- KISS: STRONG. Single pure-Python module, one dependency (wcwidth), optional cjk extra. Recent perf work was byte-identical micro-opt, not added complexity.
- Honest docs: STRONG. README example runs correctly; docs/API draw()->str matches fixed behavior; FUNCTIONAL_SPEC aligned to 1.2.x; CHANGELOG accurate EXCEPT the version-heading mismatch (REL1).
