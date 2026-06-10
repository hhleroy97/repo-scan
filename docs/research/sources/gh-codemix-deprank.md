---
id: "gh-codemix-deprank"
type: "github"
url: "https://github.com/codemix/deprank"
raw_url: "https://github.com/codemix/deprank"
tags: ["codebase-analysis", "dependency-cruiser", "dependency-graph", "file-ranking", "javascript", "migration", "pagerank", "repo", "static-analysis", "typescript"]
linked_files: []
relevance: "Provides a concrete, dependency-graph-based alternative to heuristic file-importance ranking for repo-scan when prioritizing which files to analyze, summarize, or migrate first in JavaScript and TypeScript repositories."
ingested_at: "2026-06-09 23:40 UTC"
---

# codemix/deprank — Use PageRank to find the most important files in your codebase.

## Summary

Deprank is a TypeScript CLI that uses dependency-cruiser to build a JavaScript/TypeScript import graph and applies PageRank to rank files by how widely they are depended on, directly or indirectly. It targets teams migrating large JS codebases to TypeScript by suggesting a conversion order that starts with the most foundational files. The tool outputs filename, line count, dependent count, and PageRank score, with a `--deps-first` mode that prioritizes upstream dependencies of high-rank files.

## Key claims

- PageRank over a dependency graph identifies the most important files in a JS/TS codebase, where importance means being depended on by many other files
- Converting to TypeScript in strict PageRank order increases type precision, reduces `any` usage, and minimizes rework compared with ad-hoc conversion
- The `--deps-first` option surfaces upstream dependencies of high-importance files so type errors can be fixed at their origin rather than at call sites
- Fixing a few high-rank files can eliminate hundreds or thousands of downstream type errors by improving TypeScript inference
- dependency-cruiser is used to construct the file-level dependency graph that PageRank operates on

## Notes

_yours to annotate_
