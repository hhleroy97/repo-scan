---
type: "analysis"
problem: "Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-XAMPPRocky-tokei", "gh-pytest-dev-pytest", "gh-github-linguist"]
generated_at: "2026-06-10 04:03 UTC"
linked_files: ["repo_scan/languages.py", "tests/test_languages.py", "tests/test_portability.py", "tests/test_scan.py"]
---

# Analysis — Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 04:03 UTC — confidence: high_

## Findings

- All CC 18 sits in `get_line_counts`; `detect_languages` is a simple extension walk with low complexity. The refactor target is the dual-path line counter, not language bucketing.
- Tokei is already the preferred path when installed (`tokei --output json`), parsing `reports[].stats.code` (SLOC) rather than raw line count. The UTF-8 `splitlines()` fallback counts every line, so the two paths are semantically different and tests must cover both independently.
- Filtering logic is duplicated across `detect_languages` and `get_line_counts`: `exclude_dirs`, `docs_dir`, and `LOCKFILES`. A shared `_should_skip(path, cfg)` helper would cut duplication and is the main extraction lever for lowering CC.
- `detect_languages` is partially covered in `tests/test_scan.py`; `get_line_counts` has only a lockfile regression in `tests/test_portability.py`. The tokei JSON parse path, malformed-JSON fallback, exclude-dir/docs_dir filtering, and relative-path normalization are untested.
- Linguist’s layered detection (filename → extension → heuristics, vendored/generated filtering) is richer than repo-scan’s three-bucket model. The refactor should preserve current TS/Py/C extension sets and behavior; Linguist is a reference for edge-case documentation, not a scope expansion.
- pytest `monkeypatch` on `tool_available` and `run` is the right way to stub the tokei path deterministically, matching the repo’s writers/scanner refactor precedent (characterization before extraction).
- Downstream consumers (`scanner.py`, `writers.py`, `handoff.py`, hub) depend on `line_counts` shape `{rel_path: {lines, bytes}}` and `languages` bucket counts. Output contract must stay stable through the refactor.
- Acceptance criteria require every function below rank C (CC ≤ 10) and a dedicated passing test file; trend metrics should confirm the hotspot drop after extraction.

## Recommendation

Follow the repo’s snapshot-then-extract pattern: Phase 1 adds `tests/test_languages.py` with fixture repos, monkeypatched tokei JSON (success, malformed, missing keys), fallback-path cases, and parametrized skip rules for exclude dirs, docs_dir, and lockfiles—before any production edits. Phase 2 extracts `_should_skip`, `_parse_tokei_json`, and `_fallback_line_counts` from `get_line_counts` in small commits until each function is rank B or better, without changing public signatures or scan artifact semantics.

## Risks

- Refactoring without full dual-path test coverage could silently change `scan.json` line metrics and health alerts that depend on size thresholds.
- Tokei JSON schema assumptions (`reports`, `stats.code`, `name`) may drift across tokei versions; tests should pin representative payloads, not live CLI output.
- Extracting skip logic into a shared helper risks diverging `detect_languages` and `get_line_counts` filter semantics if docs_dir or lockfile rules are applied inconsistently.
- Scope creep toward Linguist-style detection or mandatory tokei would expand the module’s responsibility beyond the ticket’s complexity-reduction goal.

## Evidence

- [[gh-XAMPPRocky-tokei\|XAMPPRocky/tokei — Count your code, quickly.]]
- [[gh-pytest-dev-pytest\|pytest-dev/pytest — The pytest framework makes it easy to write small tests, yet scales to support…]]
- [[gh-github-linguist\|github/linguist — Language Savant. If your repository's language is being reported incorrectly,…]]
- research run: [[2026-06-10-refactor-repo-scan-languages-py-cc-18-3]]
