---
type: "spec"
problem: "Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-languages-py-cc-18-3-analysis]]"
drafted_at: "2026-06-10 04:11 UTC"
---

# Spec — Refactor repo_scan/languages.py (CC 18, 3 commits, untested). `repo_scan/languages.py` is both high-churn (3 commits) and high-complexity (total CC 18) with no matching test file. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 04:11 UTC by radar — **status: approved**_

## Goal

Lower cyclomatic complexity in `repo_scan/languages.py` so every function is radon rank B or better (CC ≤ 10), with `get_line_counts` as the sole rank-C hotspot today (CC 18). Extend coverage before production edits: existing tests (`test_scan.py::test_detect_languages_buckets`, `test_portability.py::test_lockfiles_excluded_from_line_counts`) cover happy-path detection and lockfile exclusion but not dual counting paths, skip-rule matrix, or tokei failure modes. Preserve public signatures and downstream contracts: `detect_languages` → `{"ts"|"py"|"c": list[Path]}` (absolute paths from `rglob`); `get_line_counts` → `{rel_path: {"lines": int, "bytes": int}}` (repo-relative string keys).

## Approach

**Phase 1 — Characterization tests (no production changes).** Follow the writers/scanner snapshot-then-extract precedent. Add `tests/test_languages.py` with small fixture trees under `tmp_path`, monkeypatching `repo_scan.languages.tool_available` and `repo_scan.languages.run` (not subprocess) for deterministic tokei behavior. Cover both counting paths independently—they are semantically different: tokei reports SLOC via `stats.code`; the UTF-8 `splitlines()` fallback counts every line.

| Area | Cases |
|------|--------|
| Tokei path | Valid JSON with `reports[].stats.code`; `tool_available` False → fallback; malformed JSON → fallback; missing keys → fallback; non-zero exit → fallback |
| Fallback path | Extension filter (TS/Py/C only); UTF-8 read; `OSError` skip |
| Skip rules | Parametrize `exclude_dirs`, `docs_dir`, `LOCKFILES` for `get_line_counts`; `exclude_dirs` only for `detect_languages` |
| Paths | `relative_to(root)` normalization; absolute paths outside root kept as-is (tokei `ValueError` branch) |

Keep existing coverage in `tests/test_scan.py` and `tests/test_portability.py`; do not fix surprising behavior during characterization. Commit tests green against current code.

**Phase 2 — Extract Method (behavior-preserving).** Capture radon/lizard baseline on current `languages.py` (and `docs/scan.json` CC snapshot if present) before first edit; re-run after each commit and compare against baseline, not a post-refactor re-scan alone. One private helper per commit; full suite after each:

1. `_should_skip(rel: Path, cfg: dict, *, skip_docs: bool, skip_lockfiles: bool) -> bool` — unify duplicated filter logic; wire into both callers: `detect_languages` passes `skip_docs=False, skip_lockfiles=False`; `get_line_counts` passes `skip_docs=True, skip_lockfiles=True`.
2. `_parse_tokei_json(out: str, root: Path, cfg: dict) -> dict[str, dict] | None` — JSON parse, report walk, skip filter, byte stat; return `None` on decode/key errors. If radon still ranks C, sub-split (e.g. `_iter_tokei_reports`, `_tokei_entry`) before proceeding.
3. `_fallback_line_counts(root: Path, cfg: dict) -> dict[str, dict]` — extension walk + `splitlines()` count.

`get_line_counts` becomes a thin coordinator: probe tokei → parse or fallback. Confirm every function in `languages.py` is rank B or better; trend log should show hotspot reduction vs Phase 2 baseline.

## Changes

- **`tests/test_languages.py`** (new) — Fixture repos; monkeypatched tokei stubs; parametrized skip-rule matrix; separate assertions per counting path.
- **`repo_scan/languages.py`** — Phase 2 only: add `_should_skip`, `_parse_tokei_json`, `_fallback_line_counts`; refactor internals of `detect_languages` and `get_line_counts` (public signatures, return shapes, and observable behavior unchanged); `LOCKFILES` and extension sets untouched.
- **`tests/test_scan.py`** — No duplicate `detect_languages` coverage; optional import of shared fixture helper only.
- **`tests/test_portability.py`** — Keep lockfile regression unless moved deliberately with identical assertion; consider monkeypatching `tool_available`/`run` so CI does not depend on real tokei.
- **`docs/reports/health.md`** / trend log — Updated on next scan; baseline captured manually before Phase 2 for before/after comparison.

## Risks

- **`_should_skip` semantics drift** — `detect_languages` currently ignores `docs_dir` and lockfiles; a shared helper must not widen/narrow either path unintentionally. Parametrized tests are the guard.
- **Dual-path test gaps** — Asserting only one path (or conflating SLOC with raw lines) yields false confidence; stub `tool_available` explicitly per test.
- **`test_portability` tokei coupling** — Lockfile regression runs without monkeypatch today; behavior may differ when real tokei is installed vs fallback-only environments.
- **Tokei JSON shape** — Real tokei versions may differ; characterization uses minimal valid payloads; integration smoke with real tokei stays optional/`skipif`.
- **Incomplete CC reduction** — `_parse_tokei_json` may remain rank C after first extraction; sub-split contingency required before closing Phase 2.
- **Trend verification without baseline** — Re-scanning after edits mutates `docs/scan.json`; compare against pre-Phase-2 radon output, not post-hoc trend alone.
- **Churn on a small hub** — `scanner.py`, `writers.py`, `handoff.py`, and hub read `line_counts`/`languages`; one extraction per commit limits bisect pain.

## Out of scope

- Expanding language buckets or adopting Linguist-style heuristics (filename rules, vendored/generated detection).
- Changing extension sets (`TS_EXTENSIONS`, `PY_EXTENSIONS`, `C_EXTENSIONS`) or `LOCKFILES` membership.
- Replacing tokei with another counter or unifying SLOC vs raw-line semantics across paths.
- Refactoring `scanner.py` orchestration or `writers.py` report formatting.
- Public API changes (`detect_languages` / `get_line_counts` signatures or return shapes).
- Moving tests into a shared `conftest` fixture tree unless duplication becomes painful after Phase 1.

## Audit

> [!warning] Audit verdict: revise
> The phased characterization-then-extract plan, CC targets, skip-flag design, and public API preservation align well with the code and tkt-0004, but the spec should correct the precedent wording, fix the tokei JSON/fixture contract, document the tokei-vs-fallback extension-scope asymmetry, and add explicit trend verification before human review.
> - Phase 1 labels the approach 'writers/scanner snapshot-then-extract precedent,' but this spec plans monkeypatched unit tests in test_languages.py, not syrupy byte-identical artifact snapshots; test_scanner_snapshots.py does not exist yet, so only the writers refactor is an executed precedent and the wording overstates evidence.
> - The tokei-path test table says 'Valid JSON with reports[].stats.code,' but get_line_counts walks data.values() and then lang_data.get('reports', []); fixtures must use language-keyed top-level objects, not a bare reports array, or Phase 1 tests will not characterize real parsing.
> - A major dual-path semantic gap is omitted: the tokei branch does not apply TS/Py/C extension filtering (only skip dirs, docs_dir, and LOCKFILES), while the fallback branch does; Phase 1 only lists extension filter under fallback, so tests could pass while missing cross-path scope drift and health/ranking key differences.
> - Research finding that exclude_dirs, docs_dir, and LOCKFILES are duplicated in detect_languages is carried into the narrative implicitly, but detect_languages only honors exclude_dirs today; the spec's skip-flag design fixes that, yet the duplicated-filter story should not justify widening detect_languages behavior.
> - tkt-0004 requires a trend delta confirming complexity drop; the spec mentions capturing a pre-Phase-2 baseline and updating health.md on the next scan, but unlike sibling scanner/graphs specs it lacks an explicit Phase 3 self-repo scan / cc_by_file verification step, leaving acceptance criteria under-specified.
> - Existing indirect coverage in tests/test_phase_a.py (detect_languages + get_line_counts on tmp_repo_with_imports) is not inventoried; refactors could break digest wiring without any spec-listed guard beyond new unit tests.
> - test_scan.py::test_scan_writes_expected_files only asserts artifact existence, not line-count or health content, so Phase 2 could change scan.json line metrics without failing CI unless test_languages.py or an optional full-scan assertion catches it — a missing regression risk for downstream size thresholds.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-languages-py-cc-18-3-analysis]]
