---
type: "analysis"
problem: "Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint."
confidence: "medium"
sources: ["gh-networkx-networkx", "gh-phoenix-assistant-impact-graph"]
generated_at: "2026-06-09 23:46 UTC"
linked_files: ["repo_scan/ranking.py"]
---

# Analysis — Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint.
_Generated 2026-06-09 23:46 UTC — confidence: medium_

## Findings

- repo-scan already documents its composite score as a deliberate stand-in for aider-style PageRank, but the structural term is normalized in-degree (direct imports only), which under-ranks transitively important hub modules.
- Aider's repomap validates production use of personalized PageRank over a richer symbol/reference graph via networkx.pagerank, but it optimizes for LLM context packing—not repo-scan's 'start here' onboarding table.
- The arXiv documentation-prioritization study provides external evidence that PageRank over module dependency graphs beats naive centrality and supervised baselines for identifying structurally important components, with no training data required.
- deprank demonstrates file-level import-graph PageRank in roughly 50 lines of inline power iteration, directly satisfying repo-scan's zero-required-dependencies constraint (dependencies = [] in pyproject.toml).
- phoenix-assistant/impact-graph mirrors repo-scan's composite design pattern: inline iterative PageRank for structural importance plus separate depth/churn-like signals, without pulling in NetworkX.
- NetworkX is the canonical Python PageRank implementation and what aider relies on, but it introduces a non-trivial transitive dependency tree solely to run one algorithm on graphs that are typically modest in size—poor fit for a pip-install-with-zero-deps tool.
- Churn and complexity are already decoupled elsewhere in repo-scan (candidates.md, radar pick_candidate uses churn × complexity), so graph-based structural rank and maintenance-risk signals serve different purposes and need not be collapsed into PageRank alone.
- repo-scan already collects dep_edges from Python and TypeScript scans; upgrading the centrality term to PageRank is an incremental change to ranking.py, not a new data pipeline.

## Recommendation

Do not fully replace the composite heuristic with graph-only PageRank. Instead, upgrade the structural centrality term from in-degree to a lightweight inline PageRank over existing dep_edges, then keep churn, complexity, and size as separate weighted signals in the composite score. Do not add networkx—implement power iteration locally as deprank and impact-graph do, and expose the raw PageRank score in ranking output for transparency and future tuning.

## Risks

- Static import parsing misses dynamic imports, conditional imports, and re-exports, so both in-degree and PageRank rankings can be wrong on real codebases.
- Rankings will shift versus the current heuristic, which may surprise users and require updating tests and docs that describe 'import centrality'.
- Disconnected or very sparse graphs produce degenerate or unstable PageRank scores without explicit handling of dangling nodes and zero-outdegree files.
- File-level PageRank is a coarser approximation than aider's symbol-level personalized graph, so parity with repomap quality should not be expected.
- A self-implemented PageRank needs convergence tuning and regression tests; subtle bugs could silently produce misleading 'most important files' tables.

## Evidence

- [[gh-networkx-networkx\|networkx/networkx — Network Analysis in Python]]
- [[gh-phoenix-assistant-impact-graph\|phoenix-assistant/impact-graph — If I change this function, what breaks? Change impact analysis with call graphs…]]
- research run: [[2026-06-09-should-repo-scan-replace-its-heuristic-i]]
