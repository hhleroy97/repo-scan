---
id: "arxiv-2302.09153"
type: "arxiv"
url: "https://arxiv.org/abs/2302.09153"
raw_url: "https://arxiv.org/pdf/2302.09153"
tags: ["change-proneness", "co-change-analysis", "dependency-analysis", "large-active-files", "paper", "refactoring", "revision-history", "software-architecture", "technical-debt"]
linked_files: []
relevance: "For repo-scan, this supports identifying high-impact decomposition targets by combining file activity metrics with co-change and dependency signals, rather than flagging large files that rarely change."
ingested_at: "2026-06-10 17:13 UTC"
---

# Towards the Assisted Decomposition of Large-Active Files

## Summary

This arXiv paper by Lefever, Cai, Kazman, and Fang proposes a refactoring recommendation system for decomposing large-active files—change-prone, tightly coupled source files that concentrate technical debt and coordination costs. Recommendations are derived from revision history, co-change patterns, and mutual dependencies, each mapping to a distinct responsibility the file holds in the system. The approach aims to focus refactoring effort on genuinely problematic, change-prone responsibilities rather than superficially large but stable code.

## Key claims

- Large-active files—large, change-prone, interdependent source files—are a major source of technical debt that increases coordination costs and error rates.
- Decomposition recommendations should be grounded in co-change and mutual dependency analysis, not file size alone.
- Each recommendation corresponds to a specific responsibility the large-active file has relative to the rest of the system.
- Incorporating revision history into both determining and ranking recommendations avoids wasting effort on code that only appears problematic superficially.
- Moving recommended functionality into smaller files reduces the blast radius of debt-laden files and clarifies their essential responsibilities.

## Notes

_yours to annotate_
