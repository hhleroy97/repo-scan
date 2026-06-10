---
type: "spec"
problem: "Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-09-should-repo-scan-replace-its-heuristic-i-analysis]]"
drafted_at: "2026-06-09 23:48 UTC"
---

# Spec — Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint.
_Drafted 2026-06-09 23:48 UTC by radar — **status: approved**_

## Goal

Upgrade the structural term in repo-scan's important-files ranking from normalized in-degree to PageRank over the existing import dependency graph, so transitively depended-on hub modules rank higher. Keep the composite score (PageRank × churn × complexity × size) and the zero-required-dependencies constraint; do not add NetworkX.

## Approach

Add a small inline power-iteration PageRank in `ranking.py`, built from `dep_edges` already produced by Python/TS scans. Map module-level edges to file paths via existing `_module_to_file`, build a directed adjacency list (src imports dst → edge src → dst), and run standard damped PageRank with dangling-node redistribution (~50 lines, following deprank patterns).

**Node set:** all file paths in `line_counts` (same ranking universe as today). **Edgeless fallback:** if zero resolvable mapped edges exist, set `pagerank[f] = 0` for every file and skip iteration—do not run all-dangling PageRank (that would yield uniform ~1/n and centrality 1 everywhere). **Isolated files:** paths with no incident mapped edges get `pagerank = 0`; only files participating in at least one mapped edge enter the iteration (still keyed over full `line_counts`).

Use normalized PageRank as the **centrality** term in the existing composite formula (weights unchanged: 0.35 / 0.30 / 0.25 / 0.10). Retain direct in-degree as `imported_by` for transparency; add raw `pagerank` to each ranked row. Disconnected subgraphs still receive nonzero distributed rank within components—only the no-edges-at-all case matches today's all-zero centrality. No new scan pipeline, no change to radar's separate churn × complexity candidate selection.

Default parameters: damping `α = 0.85`, max iterations 100, tolerance `1e-6` L1 delta.

## Changes

- **`repo_scan/ranking.py`**
  - Add `_build_file_adjacency(dep_edges, line_counts) -> dict[str, list[str]]` mapping resolved file paths to out-neighbors; drop unmapped edges as today.
  - Add `_pagerank(nodes, adjacency, *, alpha=0.85, max_iter=100, tol=1e-6) -> dict[str, float]` with dangling-node redistribution; caller passes only edge-incident nodes when edges exist.
  - Replace in-degree normalization with `pagerank[f] / max_pagerank` (max over files with `pagerank > 0`; if all zero, centrality term 0); keep `imported_by` as direct in-degree count.
  - Extend return dict with `"pagerank": round(..., 6)`; update module docstring (PageRank centrality, not in-degree proxy).

- **`repo_scan/writers.py`**
  - Update "Start here" table caption and columns: add PageRank column; clarify "Imported by" is direct dependents only.

- **`repo_scan/digest.py`**
  - Include PageRank in the "Most important files" bullet text.

- **`tests/test_phase_a.py`**
  - Add unit tests for `_pagerank`: star graph (hub beats leaf), chain (middle node > leaf), empty graph, dangling node.
  - Extend `test_rank_files_orders_by_signals` with a chain (e.g. `a→b→c→d`) where `b`, `c`, `d` tie on `imported_by=1` but PageRank orders `d` above intermediates; assert `pagerank` key present and ordering matches expectation.
  - Add edgeless-repo case: many `line_counts` files, no mapped edges → all `pagerank` zero, centrality term zero.

- **`tests/test_radar_full.py`** (if ranking assertions exist)
  - Update field expectations for new `pagerank` field and any ordering changes.

- **Docs**
  - Brief note in README or health-report copy that structural rank uses import-graph PageRank, not direct in-degree alone.
  - Record decision in `docs/research/decisions.md` (already approved).

## Risks

- **Static graph quality**: regex-based import parsing misses dynamic/conditional imports; PageRank inherits the same blind spots as in-degree, but ranking shifts may be more visible on hub-heavy layouts.
- **Behavior change**: files with low direct in-degree but high transitive importance will rise; ordering assertions and generated "Start here" copy need updating (no golden ranking-score snapshots today).
- **Correctness**: hand-rolled power iteration must handle dangling nodes and normalization; bugs could silently skew rankings—mitigate with focused graph fixtures and edgeless/isolated-node unit tests.
- **Mixed module/path edges**: Python module names vs TS relative paths must both resolve via `_module_to_file`; unmapped edges are dropped as today.
- **Coarser than repomap**: file-level import-graph PageRank approximates structural importance more loosely than Aider-style symbol/personalized repomap; parity with repomap is not a success criterion.
- **Sparse repos**: giving isolated files `pagerank = 0` (vs today's uniformly zero centrality when no imports resolve) lets churn/complexity/size dominate the composite more often—reordering beyond hub-heavy layouts.

## Out of scope

- Replacing the composite heuristic with graph-only PageRank.
- Adding NetworkX or any new `pyproject.toml` dependencies.
- Aider-style personalized PageRank over symbol/reference graphs.
- New edge collection, call-graph integration, or weighted edges.
- Changing radar `pick_candidate` / `candidates.md` churn × complexity logic.
- Tuning composite weights or exposing PageRank-damping CLI flags (future work).

## Audit

**Verdict:** revise  |  The spec aligns with the approved analysis and zero-deps constraint, but needs clearer edge-mapping rules, corrected risk framing, and explicit coverage for importer-only and disconnected-subgraph behavior before human review.

- Approach says adjacency should 'drop unmapped edges as today,' but today's in-degree path only resolves dst via _module_to_file and never validates src; PageRank adjacency requires both endpoints to map, so edge retention is stricter and should be stated explicitly.
- Sparse-repos risk mischaracterizes the baseline: when no imports resolve, current code already yields centrality 0 for every file (max_deg falls back to 1); the real reordering drivers are PageRank tie-breaking among equal imported_by counts and nonzero centrality for importer-only files that have outgoing edges but imported_by=0.
- Importer-only files (incident edges, imported_by=0) can receive nonzero PageRank and thus a nonzero centrality term, whereas today their centrality is always 0; this behavior change is not called out in Risks.
- Approach claims disconnected subgraphs receive nonzero distributed rank within components, but the test plan has no fixture for two disconnected components (only edgeless, chain, star, dangling); that claim is untested.
- Docs/change list omits committed generated artifacts that still describe in-degree centrality (docs/index.md, docs/scan.json ranking rows, README/handoff copy), so human-facing output can drift until a self-scan or manual refresh.
- '~50 lines, following deprank patterns' is asserted without a verified Python reference implementation in-repo; deprank is TypeScript and impact-graph source was not ingested with algorithm detail—treat as implementation estimate, not evidence-backed fact.

## Provenance

- analysis: [[2026-06-09-should-repo-scan-replace-its-heuristic-i-analysis]]
