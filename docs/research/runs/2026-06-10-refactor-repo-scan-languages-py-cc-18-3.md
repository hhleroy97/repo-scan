---
type: "research-run"
question: "Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work."
sources: ["gh-XAMPPRocky-tokei", "gh-pytest-dev-pytest", "gh-github-linguist"]
run_at: "2026-06-10 04:03 UTC"
---

# Research run — Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work.
_Run 2026-06-10 04:03 UTC_

**Strategy:** Follow the repo's established snapshot-then-extract precedent (writers/scanner/graphs): Phase 1 adds `tests/test_languages.py` with fixture repos, monkeypatched tokei JSON, and lockfile/exclude-dir cases before touching production code; Phase 2 extracts `_should_skip`, `_parse_tokei_json`, and `_fallback_line_counts` from `get_line_counts` to reach rank B.

## Ingested

- [[sources/gh-XAMPPRocky-tokei\|XAMPPRocky/tokei — Count your code, quickly.]] — Documents the `--output json` schema (`reports`, `stats.code` vs total lines) and exclude flags that `get_line_counts` must parse correctly, which is the main driver of CC 18.
- [[sources/gh-pytest-dev-pytest\|pytest-dev/pytest — The pytest framework makes it easy to write small tests, yet scales to support…]] — Covers `monkeypatch` and parametrized fixtures for stubbing `tool_available`/`run`, enabling deterministic characterization of both the tokei path and the UTF-8 fallback path.
- [[sources/gh-github-linguist\|github/linguist — Language Savant. If your repository's language is being reported incorrectly,…]] — Canonical extension-and-filename language classification rules that inform how `detect_languages` buckets TS/Py/C files and what edge cases the refactor should preserve.
