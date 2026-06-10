---
type: "spec"
problem: "Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co-analysis]]"
drafted_at: "2026-06-10 01:57 UTC"
linked_files: ["repo_scan/scanner.py", "repo_scan/writers.py", "tests/conftest.py", "tests/test_visuals.py", "tests/test_writers_snapshots.py"]
---

# Spec — Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 01:57 UTC by radar — **status: approved**_

---
## Goal

Reduce cyclomatic complexity in `repo_scan/writers.py` (module CC ~52, concentrated in `write_health_report` ~28 and `write_index` ~24) without changing generated artifact semantics. Establish a regression baseline for all report writers before structural change, then split long markdown assemblers via Extract Function while keeping public `write_*` signatures stable for the implicit `scanner.py` contract.

## Approach

**Phase 1 — Characterization tests (no production refactor).** Add syrupy as a dev-only dependency. Build a fixed fixture repo (multi-file tree, line-count thresholds, manifests/entry points, `.repo-scan.json`) and invoke each `write_*` directly with deterministic synthetic inputs: `ranking`, `tree`, `delta`, `py_edges`/`ts_edges`, mermaid strings, and behavior payloads. Stub volatile output (`now_iso`, git helpers) and filesystem-dependent helpers (`trend_callout`, identity/readme paths) via monkeypatch or syrupy serializers before snapshot assertion. Snapshot full bodies at: `docs/index.md`, `docs/scan.json`, `docs/reports/{health,coupling,calls,dependencies}.md`, `docs/research/candidates.md`, and `docs/architecture/dependency-graph.md` (duplicate of dependencies report from `write_dep_report`). Commit snapshot files alongside tests; missing snapshots fail CI. Research basis is thin (Extract Function catalog, syrupy/pytest-html READMEs); Fowler Characterization Test and pytest-json-report ingest failed—treat snapshots as project-local contract, not cited methodology.

**Phase 2 — Extract Function (behavior-preserving).** Follow a data → sections → write split modeled on pytest-html’s prepare/render/I/O separation, without a template engine:

1. Pure section builders return `list[str]` (markdown) or `dict` (`scan.json` payload).
2. Thin `write_*` wrappers assemble sections, call `write_doc` / `json.dump`, unchanged paths under `cfg["docs_dir"]`.

Prioritize `write_health_report` and `write_index`; defer smaller writers until function-level ranks improve. Re-run snapshots after each extraction; CC should drop in extracted parents per conditional block moved.

**Phase 3 — Verify.** Confirm every function in `writers.py` is below radon rank C (rank B or better, CC ≤10) per tkt-0001—not merely parent hotspots ≤15. Note file-aggregate CC may remain ~52 until helpers are also split; track per-function ranks, not module sum alone. Existing tests green; no `scanner.py` signature changes.

## Changes

- **`pyproject.toml`** — Add `[project.optional-dependencies] dev` with `pytest` and `syrupy`; document `pip install -e ".[dev]"`.
- **`.github/workflows/ci.yml`** — Replace `pip install pytest` with `pip install -e ".[dev]"` so syrupy snapshots run in CI.
- **`tests/conftest.py`** — Add `writers_fixture_repo` (nested dirs, large file, manifests, entry points, `.repo-scan.json`) plus fixtures stubbing `now_iso`, `git_branch`, `git_last_commit`, `git_remote_url`, `trend_callout`, and identity/readme filesystem reads to fixed values.
- **`tests/test_writers_snapshots.py`** (new) — Direct calls to all `write_*` except `write_agents_md` (covered in `test_phase_a.py`); syrupy snapshots per artifact path above; explicit `schema_version` (and optionally cfg subset) assertion on `scan.json` to catch intentional schema bumps without relying on full-file diff alone.
- **`tests/test_visuals.py`** — Keep unit scope on visual helpers and fragment checks; avoid duplicating full-artifact snapshots.
- **`repo_scan/writers.py`** — Phase 2 only, after snapshots land:
  - Extract from `write_health_report`: directory rollup + pie, file-size table, complexity table, churn chart/table, ownership table, action-item callout → e.g. `_health_*_section` helpers.
  - Extract from `write_index`: summary callouts, overview table, ranking/tree sections → e.g. `_index_*_section` helpers.
  - Extract from `write_scan_json`: payload dict builder separate from file I/O.
  - Optionally apply same pattern to `write_coupling_report`, `write_candidates`, dep/call reports if any function remains rank C or worse.
  - Leave `callout`, `mermaid_*`, `write_agents_md` untouched unless moved for grouping only.
- **`repo_scan/scanner.py`** — No changes expected; import list and call order unchanged.
- **`docs/`** (optional) — Brief note in contributor/testing docs on updating syrupy snapshots when output intentionally changes.

## Risks

- Snapshots fail on any formatting drift; volatile metadata and filesystem-dependent helpers must be stubbed consistently or normalization will cause false positives.
- Full-file `scan.json` snapshots churn on `cfg` key additions or ordering; pair with explicit `schema_version` and targeted field tests when bumping structure.
- Full-file snapshots may hide intentional schema edits; do not rely on them alone for structural changes.
- Over-extraction into many one-liner helpers can raise churn without lowering CC if conditionals stay in parents.
- New dev dependency requires CI `.[dev]` install; runtime zero-dependency constraint preserved only if syrupy stays dev-scoped.
- Hidden `scanner.py` ↔ `writers.py` coupling (~67%) means coordinated edits remain likely; signature stability is critical.
- Characterization-test methodology is lightly sourced; snapshot failures are the authoritative regression signal.

## Out of scope

- Template engine or Jinja/Mustache adoption for markdown reports.
- Refactoring `scanner.py` orchestration or merging writers into another module.
- Changing report content, thresholds, Mermaid syntax, or file layout paths.
- Replacing fragment-based integration tests in `test_scan.py` / `test_visuals.py` wholesale.
- Runtime dependency additions beyond dev test tooling.
- RADAR pipeline changes or LLM-related writer behavior.
---

## Audit

> [!warning] Audit verdict: revise
> The phased snapshot-then-extract plan matches the codebase hotspots and ticket intent, but the spec needs aligned verification against tkt-0001 trend metrics, tighter research citations, and corrected CI/pytest dependency details before review.
> - Phase 3 Verify omits tkt-0001 acceptance criterion 'Trend delta confirms complexity drop'—no step to re-run repo-scan and assert writers.py cc_by_file / hotspot metrics improved after refactor.
> - Phase 3 note that file-aggregate CC may remain ~52 contradicts how the project measures trend delta: cc_by_file sums only rank-C+ functions (currently 28+24=52); splitting the two D-rank parents below C should drive that file metric toward 0, which is what the ticket expects.
> - pytest-html prepare/render/I/O separation is cited as structural guidance but the ingested pytest-html source only documents HTML test-report CLI/hooks, not a document-assembly layering pattern—unsupported by listed research.
> - CI Changes misstate the workflow: ci.yml runs `pip install -e .` then `pip install pytest radon lizard`, not standalone `pip install pytest`; dev-deps plan should say whether radon/lizard stay as separate CI installs.
> - Syrupy 5.x requires pytest>=8 per ingested syrupy source; spec adds pytest to dev deps without a minimum version or pin—missing constraint/risk.
> - Deferral of smaller writers 'until function-level ranks improve' is misleading: only write_health_report (D/28) and write_index (D/24) fail acceptance; all other writers are already rank B or better.
> - Research basis cites 'pytest-html READMEs' alongside thin characterization-test sourcing, but Fowler Characterization Test and pytest-json-report ingest failed—only Extract Function and syrupy are substantively ingested.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co-analysis]]
