---
type: "spec"
problem: "Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-analysis]]"
drafted_at: "2026-06-10 03:51 UTC"
---

# Spec — Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 03:51 UTC by radar — **status: approved**_

## Goal

Reduce cyclomatic complexity in `repo_scan/graphs.py` (module CC 56; four rank-C hotspots: `get_python_dep_edges` CC 19, `edges_to_mermaid` CC 13, `get_ts_dep_edges` CC 12, `get_c_call_graph_mermaid` CC 12) without changing scan artifacts, PageRank node keys, or Mermaid output unless characterization exposes a pre-existing bug. Add `tests/test_graphs.py` for direct edge/Mermaid contracts (existing coverage in `test_visuals.py`, `test_scan.py`, `test_portability.py`, and `test_phase_a.py` is thin or indirect). Meet tkt-0003: every function in `graphs.py` rank D or better (CC ≤10), test file passes, trend delta shows `graphs.py` hotspot reduction.

## Approach

**Phase 1 — Characterization tests (no production changes).** Lock current behavior via project-local snapshot contracts (writers precedent); no production edits.

Add `tests/test_graphs.py` with local fixture repos and monkeypatched `run` / `tool_available` so CI never depends on madge or cflow binaries.

- **`edges_to_mermaid`** — Full golden matrix here: deduped edges, empty-input `None`, PageRank hot/warm/cold tiers. `test_visuals.py` keeps smoke tests only; no duplicated tier matrix.
- **`get_python_dep_edges`** — Fixture tree covering simple `import`/`from`, package `__init__.py` (lock `repo_modules` dir-key vs `src_mod` `__init__.py`-suffix asymmetry), `exclude_dirs`, and known regex gaps (parenthesized/multiline/relative imports).
- **`get_ts_dep_edges`** — Monkeypatched madge JSON for `src/`, `app/`, and repo-root layouts; assert path re-anchoring (`prefix + src`) matches ranking keys; cover empty graph, bad JSON, missing tool, and skip reasons.
- **`get_c_call_graph_mermaid`** — Fixture cflow indented output; depth/stack edge cases; `None` when tool missing or empty.
- **`get_python_dep_graph_mermaid`** — Thin composition test (edges → mermaid).

Assert `(src, dst)` edge tuples and full Mermaid strings byte-for-byte. Do not fix surprising behavior; document intentional bugs for Phase 2 triage. Re-run existing `test_scan.py` / `test_visuals.py` unchanged.

**Phase 2 — Extract and simplify (behavior-preserving).** One logical commit per extraction; full suite green after each. All four rank-C functions must clear the gate.

1. Extract pure helpers not yet present: `_path_to_module(rel: Path) -> str`, `_build_repo_module_index(py_files, root) -> set[str]`; reuse existing `_node_id`.
2. Replace `get_python_dep_edges` line heuristics with stdlib `ast` import walking. Resolve intra-repo targets against the module index; preserve Phase 1 goldens unless a characterized bug is explicitly fixed with snapshot update.
3. Simplify `get_ts_dep_edges` and `get_c_call_graph_mermaid` via extracted parse/normalize helpers (prefix re-anchoring, JSON/cflow line parsing, skip-reason assembly) — adapter signatures and CLI flags unchanged.
4. Split `edges_to_mermaid` tier/classDef assembly into small pure helpers as needed for rank D.

Public API in `repo_scan/__init__.py` and `scanner.py` import surface unchanged. Writers snapshots remain canonical for `dependencies.md` / `dependency-graph.md`; graphs unit tests own edge/Mermaid contracts.

**Phase 3 — Verify.** Radon: every function in `graphs.py` rank D or better (CC ≤10). Per-function rank is the acceptance gate; `cc_by_file` sums only rank-C+ functions (currently 19+13+12+12=56) and may not drop until all hotspots clear. Dogfood re-scan: capture baseline `docs/scan.json` and `reports/trend.md` before refactor, then compare post-change delta for `repo_scan/graphs.py`.

## Changes

- **`tests/test_graphs.py`** (new) — Phase 1 characterization: Python import fixtures, madge/cflow monkeypatch probes, Mermaid goldens, edge-set assertions.
- **`tests/test_visuals.py`** — Keep existing `edges_to_mermaid` smoke tests only.
- **`tests/test_portability.py`** — Keep optional real-madge integration; no removal.
- **`tests/conftest.py`** — Extend only with shared stub helpers if multiple graph tests need them.
- **`repo_scan/graphs.py`** — Phase 2: module-path helpers, `ast`-based import walker, simplified adapters for all four hotspots; unchanged function signatures and return types.
- **`repo_scan/scanner.py`**, **`repo_scan/writers.py`** — No changes expected; touch only if snapshot drift reveals upstream contract bug.
- **`repo_scan/__init__.py`** — Re-export list unchanged.

## Risks

- `ast` parsing may change edge sets on relative imports, packages, and conditional imports — Phase 1 goldens are mandatory before switching parsers.
- `collect_digest_inputs()` independently calls `get_python_dep_edges` and `get_ts_dep_edges` for ranking; graphs unit tests alone may miss digest-path edge parity — spot-check digest inputs or writers snapshots after refactor.
- Python edges use dotted module names; TS edges use repo-relative file paths — both must stay compatible with `ranking._module_to_file` or PageRank hub tinting breaks even when Mermaid bytes are unchanged.
- madge path re-anchoring (`src_dir.relative_to(root)`) is fragile; prefix-logic extraction can break ranking keys without obvious Mermaid failure.
- Optional-tool tests without monkeypatching stay skip-gated or flaky; Phase 1 must not rely on host `madge`/`cflow`.
- Edge or Mermaid drift propagates to `node_scores`, `dependencies.md`, health/radar signals — writers snapshots may not isolate graphs-only regressions.
- Module split or new files increases import churn during a multi-commit hotspot window; prefer in-file extraction unless CC gate fails.

## Out of scope

- Replacing madge with another TS analyzer or pydeps as a runtime dependency.
- Changing `write_*` signatures, report layout, or PageRank tier thresholds (60% / 25%).
- Scanner `scan()` orchestration refactor (tkt-0002) or writers refactor (tkt-0001).
- Fixing all regex import blind spots in Phase 1; only lock current behavior, then improve structurally in Phase 2 with explicit snapshot updates.
- E2E duplicate of writers golden files for dependency reports.
- Template engines, new PyPI runtime dependencies, or radar/LLM pipeline changes.

## Audit

> [!warning] Audit verdict: revise
> Phasing, hotspot metrics, and research-backed ast/madge approach are sound, but radon rank wording is wrong, test_visuals Phase 1 handling contradicts itself, and __init__.py/cflow truncation contracts need explicit lock-in before review.
> - Goal and Phase 3 gate say 'rank D or better (CC ≤10)' but project radon scale maps rank D to CC 21–30 and 'below rank C' (tkt-0003) to rank B/A (CC ≤10); the parenthetical contradicts the rank letter and is weaker than the ticket if read literally.
> - Phase 1 says re-run test_scan.py / test_visuals.py unchanged, but Changes requires trimming test_visuals.py edges_to_mermaid tier coverage to smoke-only while moving the full matrix to test_graphs.py—those edits cannot be both required and unchanged.
> - Phase 2 proposes a single _path_to_module helper without requiring the characterized repo_modules vs src_mod __init__.py asymmetry (repo_modules strips __init__.py to the package dir; src_mod keeps a .__init__ suffix)—naive unification would break Phase 1 goldens.
> - get_c_call_graph_mermaid slices c_files[:30] but Phase 1 characterization does not list locking that truncation cap—an unmentioned behavioral contract.
> - Research/analysis documents partial existing coverage (test_visuals.py, test_scan.py, skip-gated test_portability.py); Goal still echoes ticket 'untested' without reconciling that framing, which can mislead reviewers about Phase 1 scope.
> - Missing risk: test_visuals.py test_dep_report_has_color_legend exercises PageRank tier Mermaid via full scan(); trimming unit tier tests without noting this integration oracle can leave tier regressions to E2E-only detection.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-analysis]]
