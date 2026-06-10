---
type: "spec"
problem: "Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-analysis]]"
drafted_at: "2026-06-10 03:24 UTC"
linked_files: ["repo_scan/scanner.py", "repo_scan/writers.py", "tests/conftest.py", "tests/test_scan.py", "tests/test_scanner_snapshots.py"]
---

# Spec — Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 03:24 UTC by radar — **status: approved**_

## Goal

Reduce cyclomatic complexity in `repo_scan/scanner.py` (`scan()` CC 28, rank D—the sole rank-C+ function; `cc_by_file` 28) without changing scan artifacts or orchestration semantics. Establish a regression baseline for the full scan pipeline and digest entry points before structural change, then decompose `scan()` via Extract Method while keeping the implicit `writers.py` contract (call order and signatures) stable.

## Approach

**Phase 1 — Characterization tests (no production changes).** Follow Feathers’ change algorithm and the writers refactor precedent: tests are a prerequisite, not a follow-on. Mirror `tests/test_writers_snapshots.py`—local `fixture_repo` in the new snapshot module (multi-file git tree, `.repo-scan.json`, churn history rich enough for ranking/graphs/radar), with monkeypatches on volatile helpers across `behavior`, `complexity`, `trends`, `tickets`, `identity`, and optional-tool probes (radon/lizard/cflow)—not a shared `conftest` fixture. Run `repo_scan.scan(root, quiet=True)` end-to-end. **Writers snapshots remain canonical** for `write_*` artifacts (`index.md`, `scan.json`, `reports/{health,coupling,calls,dependencies}.md`, `architecture/dependency-graph.md`, `research/candidates.md`); scanner E2E asserts those paths match writers golden output for the same stubbed inputs rather than maintaining duplicate syrupy files. Snapshot orchestration-only side effects: `reports/trend.md`, `docs/digest.md` (via `run_digest`), and `docs/tickets/*` when tickets are exercised. Baseline variant: `tickets_enabled=False` (or stub `generate_tickets` / `now_date`) to avoid volatile ticket mutation; add explicit variants for `include_handoff=True`, `radar_enabled=True`, and `tickets_enabled=True` with date stubs. Add direct unit tests for `ranking_node_scores`, `collect_digest_inputs`, and `run_digest` (return shape, key parity, output path). Do not fix surprising behavior during characterization. Commit snapshot files; missing snapshots fail CI.

**Phase 2 — Extract Method (behavior-preserving).** One helper per existing `step()` label—no merge/split: `_detect_languages`, `_count_lines`, `_check_git_churn`, `_analyze_behavior`, `_analyze_complexity`, `_build_dependency_graphs`, `_build_call_graphs`, `_rank_files`, `_write_reports` (includes `append_trend_log`), `_post_scan_actions` (radar, tickets, handoff, quiet output). Introduce a `ScanContext` dataclass holding cfg, languages, line_counts, churn, behavior, complexity, edges, ranking, tree, tested, node_scores, mermaid strings, summaries, delta, seams—mutated only by stage functions. Extract one stage per commit; parent `scan()` becomes a thin coordinator. Re-run full test suite after each extraction; writers snapshots and scanner orchestration snapshots must stay byte-identical.

**Phase 3 — Verify.** Confirm every function in `scanner.py` is radon rank B or better (CC ≤10 per function), not merely a lowered `scan()` parent score. Re-run repo-scan on this repo (10 commits per current `scan.json`) and assert trend/cc_by_file metrics show scanner hotspot reduction. Defer digest/scan deduplication, conditional simplification, and signature changes until Phase 3 passes.

## Changes

- **`tests/test_scanner_snapshots.py`** (new) — Local `fixture_repo` + shared input constants (writers-pattern); E2E `scan()` with flag-matrix parametrization; writers golden comparison for `write_*` paths; syrupy snapshots for `trend.md`, `digest.md`, and ticket artifacts; targeted `scan.json` field assertions.
- **`tests/test_scanner_unit.py`** (new) — Pure tests for `ranking_node_scores`, `collect_digest_inputs`, `run_digest`.
- **`tests/conftest.py`** — Keep minimal `tmp_repo` fixtures; extend only with shared stub helpers callable from snapshot modules.
- **`tests/test_scan.py`** — Keep existing existence/wikilink tests; no duplicate full-artifact snapshots.
- **`repo_scan/scanner.py`** — Phase 2 only: `ScanContext`; stage helpers 1:1 with `step()` labels; unchanged public signatures; stable `write_*` call order and argument shapes.
- **`repo_scan/writers.py`** — No changes expected; coordinated edits only if snapshot drift reveals a pre-existing contract bug (update writers snapshots first).
- **`docs/`** (optional) — Note on snapshot update order: writers golden files, then scanner orchestration snapshots.

## Risks

- Integration snapshots may miss stage-internal regressions; unit tests on extracted stages (Phase 2+) mitigate only after extraction.
- Scanner ↔ writers coupling (56% over 5 commits per `coupling.md`) means call-order or payload drift breaks reports despite stable signatures.
- Minimal `tmp_repo` fixtures lack churn/complexity/coupling richness for meaningful ranking/graph/radar characterization; writers-scale fixture weight is required.
- Incomplete stubbing across behavior/trends/tickets/identity causes brittle snapshots or false greens.
- Extracting helpers without moving conditional branches (`quiet`, radar, tickets, handoff, missing tools) raises churn without lowering CC.
- `scan()` and `collect_digest_inputs()` can diverge if deduplication is attempted before both paths are characterized.
- High churn on a coordination hub increases blast radius; one commit per stage limits bisect difficulty but lengthens the refactor window.

## Out of scope

- Merging or refactoring `repo_scan/writers.py` (already covered by tkt-0001).
- Deduplicating `collect_digest_inputs()` with `scan()` until Phase 3 CC verification passes.
- Changing report content, thresholds, ticket/radar behavior, or `write_*` signatures.
- Replacing `tests/test_scan.py` or `tests/test_writers_snapshots.py` wholesale.
- Template engines, runtime dependency additions, or RADAR/LLM pipeline changes.
- Substantive conditional simplification or new public APIs before per-function rank B is confirmed.

## Audit

> [!warning] Audit verdict: revise
> The phased snapshot-then-extract shape matches the writers precedent and scanner hotspots, but the spec needs reconciled metrics, a feasible writers-parity test design, and aligned Phase 2 extraction rules before human review.
> - Phase 2 requires one helper per existing `step()` label with no merge/split, but `_post_scan_actions` bundles radar, tickets, handoff, and quiet-output branches that have no `step()` label—an internal contradiction.
> - Writers-golden comparison for `write_*` artifacts is unjustified without a defined mechanism (e.g., shared payload constants and coordinated upstream stubs) to make the scanner E2E pipeline emit the same inputs as `tests/test_writers_snapshots.py`; those tests call `write_*` directly with synthetic dicts, not a full `scan()` run.
> - Phase 2 defers conditional relocation while Phase 3 requires every function at rank B (CC ≤10); verbatim extraction of post-write branches into `_post_scan_actions` can leave a high-CC helper with no planned follow-on split, conflicting with research finding that CC only drops when branches move out of `scan()`.
> - Goal cites CC 27 and 8 commits, but current evidence (`health.md`, `scan.json`, radon) shows `scan()` at CC 28 and 10 churn commits for `repo_scan/scanner.py`—stale metrics relative to findings.
> - Phase 1 centers E2E `scan()` but lists `docs/digest.md` among orchestration snapshots; `scan()` never calls `run_digest()`, so digest snapshot scope is only covered by separate unit tests—the Phase 1 oracle description is inconsistent.
> - Goal/problem frames the module as untested, contradicting ingested analysis finding #3 and existing `tests/test_scan.py` coverage that invokes `scan()` (existence/wikilink checks on minimal `tmp_repo`).
> - Phase 3 rank-B gate (CC ≤10) is stricter than tkt-0002 acceptance ('below rank C') without justification—scope creep beyond ticket criteria.
> - Phase 3 dogfood trend verification lacks baseline discipline: Phase 1 snapshots and any re-scan mutate `docs/scan.json` and `reports/trend.md`, confounding before/after `cc_by_file` comparison for `scanner.py`.
> - Missing risk: `reports/trend.md` snapshots depend on pre-existing `scan.json` (`load_previous_summary`) and append semantics (`append_trend_log`); spec does not require seeding or stubbing prior trend state for deterministic bytes.
> - Missing risk: Phase 2 stage list omits coordinator preamble (`load_config`, `ensure_dirs`, quiet header/printing), so extracted `scan()` may retain non-trivial CC from unassigned branches.
> - Coupling seam cited as 56% (5 commits) in Risks but research and tkt-0008 document 67%—inconsistent with ingested findings.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-analysis]]
