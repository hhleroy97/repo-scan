---
id: "url-aider-chat-docs-repomap"
type: "url"
url: "https://aider.chat/docs/repomap.html"
raw_url: "https://github.com/Aider-AI/aider/blob/main/aider/website/docs/repomap.md"
tags: ["context-engineering", "repo-map", "graph-ranking", "token-budget", "agents", "repo-scan"]
linked_files: ["repo_scan/radar/research.py", "repo_scan/digest.py", "repo_scan/ranking.py"]
relevance: "Canonical pattern for repo_snapshot: send a concise map of symbols and signatures ranked by graph relevance, not the whole repo — directly applicable to extending repo_context_snippet beyond scan.json one-liners."
ingested_at: "2026-06-10 16:00 UTC"
---

# Aider — Repository map documentation

## Summary

Aider attaches a **concise repository map** to every LLM change request: files, key classes/functions, and signature lines — not full file contents. For large repos the map is **graph-ranked** (files as nodes, dependency edges) and trimmed to a token budget (`--map-tokens`, default ~1k). The model uses the map to decide which files to pull into context next. Repo-scan already has PageRank ranking and `digest.py` token budgeting; this source validates a **ranked snapshot** approach over dumping `scan.json` or whole trees.

## Key claims

- A repo map shows *definitions* (critical lines per symbol), enough for the model to use APIs without reading every file.
- Graph ranking selects the most relevant subgraph for the current task when the full map exceeds context.
- Token budget is dynamic — expands when no files are in chat yet (whole-repo orientation pass).
- "Repository map, not RAG" — structured code graph beats naive retrieval for coding agents (Aider SWE-bench writeup).
- Complements repomix-style full-tree packing: map for orientation, selective file reads for depth.

## GitHits provenance

- Indexed via GitHits `search` on `github:Aider-AI/aider`, query `repomap repository context injection chat`
- Primary doc: `aider/website/docs/repomap.md` @ 6435cb8
- Related: `aider/repomap.py` (`RepoMap` class), blog post 2023-10-22-repomap (tree-sitter)

## Notes

_yours to annotate — Phase 1 task 1.2: `repo_snapshot()` should mirror map philosophy using scan.json ranking + health hotspots, not repomix XML._
