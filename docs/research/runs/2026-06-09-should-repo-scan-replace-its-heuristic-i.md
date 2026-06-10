---
type: "research-run"
question: "Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint."
sources: ["gh-networkx-networkx", "gh-phoenix-assistant-impact-graph"]
run_at: "2026-06-09 23:46 UTC"
---

# Research run — Should repo-scan replace its heuristic important-files ranking (centrality x churn x complexity) with a PageRank-style algorithm over the dependency graph, like aider's repomap does? Consider whether networkx is worth adding given the zero-required-dependencies design constraint.
_Run 2026-06-09 23:46 UTC_

**Strategy:** Build on already-ingested aider, deprank, and arxiv-2006.10892 by closing two gaps: empirical evidence that in-degree ≠ PageRank on code graphs, and a concrete audit of what NetworkX actually buys versus an inline power-iteration port. Prioritize sources that treat graph centrality as one signal among churn and complexity, not a full replacement.

## Ingested

- [[sources/gh-networkx-networkx\|networkx/networkx — Network Analysis in Python]] — Inspect `pagerank_alg.py` to see exactly what aider's repomap relies on—personalization, dangling-node handling, and power iteration—and whether that ~150-line pure-Python core is worth vendoring instead of adding the full library.
- [[sources/gh-phoenix-assistant-impact-graph\|phoenix-assistant/impact-graph — If I change this function, what breaks? Change impact analysis with call graphs…]] — Production-style file/call-graph tool that ranks change risk with inline iterative PageRank plus separate depth/churn-like signals, mirroring repo-scan's composite goal without NetworkX.

## Failed

- `url:https://onlinelibrary.wiley.com/doi/10.1155/2014/237243` — fetch failed for https://onlinelibrary.wiley.com/doi/10.1155/2014/237243: HTTP Error 403: Forbidden
