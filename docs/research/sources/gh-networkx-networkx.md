---
id: "gh-networkx-networkx"
type: "github"
url: "https://github.com/networkx/networkx"
raw_url: "https://github.com/networkx/networkx"
tags: ["codebase-analysis", "complex-networks", "dependency-graph", "graph-algorithms", "graph-analysis", "graph-theory", "graph-visualization", "library", "pagerank", "python", "repo"]
linked_files: ["repo_scan/graphs.py"]
relevance: "Reference implementation for PageRank-based file or module importance ranking over dependency graphs—the pattern aider’s repomap uses and repo-scan is evaluating against its zero-required-dependencies constraint."
ingested_at: "2026-06-09 23:43 UTC"
---

# networkx/networkx — Network Analysis in Python

## Summary

NetworkX is the de facto Python library for creating, analyzing, and visualizing graphs and complex networks, with ~17k GitHub stars and very high PyPI adoption. It exposes a broad catalog of graph algorithms—including PageRank, centrality, shortest paths, and community detection—over flexible directed, undirected, weighted, and multigraph data structures. Tools such as aider use it in production to rank code reference graphs, making it the canonical implementation choice when graph-based structural ranking is needed in Python.

## Key claims

- NetworkX is the standard Python toolkit for graph construction, manipulation, analysis, and visualization
- The library implements PageRank and many other centrality and traversal algorithms over directed and undirected graphs
- Graph models support weighted edges, multigraphs, and attribute-rich nodes and edges for domain-specific metadata
- Production codebases (e.g. aider repomap) use networkx.pagerank to rank file and symbol reference graphs for LLM context selection
- The package is BSD-3-Clause licensed and distributed on PyPI with very large monthly download volume
- Adding NetworkX introduces a non-trivial transitive dependency tree compared with a small inline power-iteration implementation

## Notes

_yours to annotate_
